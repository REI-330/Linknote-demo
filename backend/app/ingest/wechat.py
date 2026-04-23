from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..config.settings import AppConfig
from ..models.ingest import CollectedInput
from .store import store_text_input
from .wechat_paths import resolve_wechat_path
from .wechat_refresh import maybe_refresh_wechat_export

try:
    import zstandard as zstd
except ImportError:
    zstd = None


WECHAT_DB_SUBDIRS = ("contact", "session", "message")
URL_PATTERN = re.compile(r"https?://[^\s<>()\[\]{}\"'`]+", re.IGNORECASE)
URL_BYTES_PATTERN = re.compile(rb"https?://[^\s<>()\[\]{}\"'`]+", re.IGNORECASE)
ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"


@dataclass(slots=True)
class WeChatSession:
    username: str
    title: str
    last_timestamp: int
    is_chatroom: bool


def _clean_url(value: str) -> str:
    return value.replace("\x00", "").rstrip(".,;:!?)>]}\"'")


def _extract_urls(text: str) -> list[str]:
    return [_clean_url(match) for match in URL_PATTERN.findall(text)]


def _maybe_decompress_message_bytes(value: bytes) -> bytes:
    if not value.startswith(ZSTD_MAGIC) or zstd is None:
        return value
    try:
        return zstd.ZstdDecompressor().decompress(value)
    except zstd.ZstdError:
        return value


def _extract_urls_from_value(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, bytes):
        decoded = _maybe_decompress_message_bytes(value)
        urls: list[str] = []
        for match in URL_BYTES_PATTERN.findall(decoded):
            cleaned = _clean_url(match.decode("utf-8", errors="ignore"))
            if cleaned:
                urls.append(cleaned)
        return urls
    return _extract_urls(str(value))


def _xml_message_preview(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("<") and not stripped.startswith("<?xml"):
        return ""
    try:
        root = ET.fromstring(stripped)
    except ET.ParseError:
        return ""

    def _node_text(path: str) -> str:
        node = root.find(path)
        if node is None or node.text is None:
            return ""
        return re.sub(r"\s+", " ", node.text).strip()

    title = _node_text(".//appmsg/title")
    desc = _node_text(".//appmsg/des")
    url = _node_text(".//appmsg/url")
    app_name = _node_text(".//appinfo/appname")

    parts = [part for part in (app_name, title, desc, url) if part]
    return " | ".join(parts)


def _message_preview(value: object, urls: list[str]) -> str:
    if isinstance(value, bytes):
        decoded_bytes = _maybe_decompress_message_bytes(value)
        text = decoded_bytes.decode("utf-8", errors="ignore").replace("\x00", " ")
        text = re.sub(r"\s+", " ", text).strip()
        xml_preview = _xml_message_preview(text)
        if xml_preview:
            return xml_preview
        text_without_urls = text
        for url in urls:
            text_without_urls = text_without_urls.replace(url, " ")
        residual_text = re.sub(r"\s+", " ", text_without_urls).strip()
        if residual_text and sum(char.isprintable() for char in residual_text) / max(len(residual_text), 1) >= 0.85:
            return text
        return " ".join(urls)
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text) or " ".join(urls)


def _wechat_account_root(config: AppConfig) -> Path:
    resolved = resolve_wechat_path(config)
    if resolved is not None:
        return resolved.account_root
    return config.wechat.chatlog_root / config.wechat.account_dir


def _wechat_live_db_root(config: AppConfig) -> Path:
    resolved = resolve_wechat_path(config)
    if resolved is not None:
        return resolved.db_root
    return _wechat_account_root(config) / "db_storage"


def _wechat_snapshot_root(config: AppConfig) -> Path:
    resolved = resolve_wechat_path(config)
    account_name = resolved.account if resolved is not None else (config.wechat.account_dir.strip() or "default")
    return config.paths.runtime_dir / "wechat_snapshot" / account_name / "db_storage"


def _normalized_session_allowlist(config: AppConfig) -> set[str]:
    return {item.casefold() for item in config.wechat.session_allowlist}


def _append_session_if_allowed(
    sessions: list[WeChatSession],
    seen_usernames: set[str],
    config: AppConfig,
    contact_titles: dict[str, str],
    username: object,
    no_contact_title: object,
    last_timestamp: object,
) -> None:
    clean_username = str(username)
    if clean_username in seen_usernames:
        return
    is_chatroom = clean_username.endswith("@chatroom")
    if is_chatroom and not config.wechat.include_chatrooms:
        return
    title = contact_titles.get(clean_username) or str(no_contact_title or "") or clean_username
    if not _session_is_allowed(config, clean_username, title):
        return
    sessions.append(
        WeChatSession(
            username=clean_username,
            title=str(title),
            last_timestamp=int(last_timestamp or 0),
            is_chatroom=is_chatroom,
        )
    )
    seen_usernames.add(clean_username)


def _session_is_allowed(config: AppConfig, username: str, title: str) -> bool:
    allowlist = _normalized_session_allowlist(config)
    if not allowlist:
        return True
    return username.casefold() in allowlist or title.casefold() in allowlist


def _iter_wechat_storage_files(source_root: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for subdir in WECHAT_DB_SUBDIRS:
        source_dir = source_root / subdir
        if not source_dir.exists():
            continue
        for source in sorted(path for path in source_dir.iterdir() if path.is_file()):
            pairs.append((source.relative_to(source_root), source))
    return pairs


def _copy_storage_file(source: Path, destination: Path) -> None:
    if source.suffix.lower() != ".db":
        shutil.copyfile(source, destination)
        return

    try:
        source_conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
        destination_conn = sqlite3.connect(destination)
        try:
            source_conn.backup(destination_conn)
            return
        finally:
            destination_conn.close()
            source_conn.close()
    except sqlite3.DatabaseError:
        shutil.copyfile(source, destination)


def _copy_wechat_snapshot(config: AppConfig) -> Path:
    source_root = _wechat_live_db_root(config)
    target_root = _wechat_snapshot_root(config)
    staging_root = target_root.parent / f"{target_root.name}.staging"
    storage_files = _iter_wechat_storage_files(source_root)

    if not storage_files:
        if target_root.exists():
            return target_root
        return source_root

    if staging_root.exists():
        shutil.rmtree(staging_root, ignore_errors=True)
    staging_root.mkdir(parents=True, exist_ok=True)

    try:
        for relative_path, source in storage_files:
            destination = staging_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            _copy_storage_file(source, destination)
    except OSError:
        shutil.rmtree(staging_root, ignore_errors=True)
        return source_root

    try:
        if target_root.exists():
            shutil.rmtree(target_root, ignore_errors=True)
        staging_root.replace(target_root)
    except OSError:
        return source_root

    return target_root


def _session_db_path(config: AppConfig, db_root: Path | None = None) -> Path:
    root = _wechat_snapshot_root(config) if db_root is None else db_root
    return root / "session" / "session.db"


def _contact_db_path(config: AppConfig, db_root: Path | None = None) -> Path:
    root = _wechat_snapshot_root(config) if db_root is None else db_root
    return root / "contact" / "contact.db"


def _message_db_paths(config: AppConfig, db_root: Path | None = None) -> list[Path]:
    root = _wechat_snapshot_root(config) if db_root is None else db_root
    message_dir = root / "message"
    return sorted([*message_dir.glob("message_[0-9]*.db"), *message_dir.glob("biz_message_[0-9]*.db")])


def _wechat_state_path(config: AppConfig) -> Path:
    return config.paths.runtime_dir / "wechat_state.json"


def _load_state(config: AppConfig) -> dict[str, object]:
    state_path = _wechat_state_path(config)
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_state(config: AppConfig, state: dict[str, object]) -> None:
    state_path = _wechat_state_path(config)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _wechat_state_key(config: AppConfig) -> str:
    resolved = resolve_wechat_path(config)
    if resolved is not None:
        return f"{resolved.account_root}|{resolved.account}"
    account = config.wechat.account_dir.strip() or "default"
    return f"{config.wechat.chatlog_root}|{account}"


def _load_last_scan_timestamp(config: AppConfig, state: dict[str, object], default_since: int) -> int:
    by_account = state.get("last_scan_by_account")
    if isinstance(by_account, dict):
        try:
            return int(by_account.get(_wechat_state_key(config), default_since))
        except (TypeError, ValueError):
            return default_since
    try:
        return int(state.get("last_scan_timestamp", default_since))
    except (TypeError, ValueError):
        return default_since


def _build_scan_state(config: AppConfig, state: dict[str, object], last_scan_timestamp: int) -> dict[str, object]:
    payload = dict(state)
    by_account_raw = state.get("last_scan_by_account")
    by_account = dict(by_account_raw) if isinstance(by_account_raw, dict) else {}
    by_account[_wechat_state_key(config)] = int(last_scan_timestamp)
    payload["last_scan_timestamp"] = int(last_scan_timestamp)
    payload["last_scan_by_account"] = by_account
    return payload


def _build_contact_titles(config: AppConfig, db_root: Path) -> dict[str, str]:
    titles: dict[str, str] = {}
    path = _contact_db_path(config, db_root)
    if not path.exists():
        return titles

    conn = sqlite3.connect(path)
    cur = conn.cursor()
    try:
        for username, remark, nick_name in cur.execute(
            "select username, ifnull(remark,''), ifnull(nick_name,'') from contact"
        ):
            display = (remark or nick_name or username).strip()
            if display:
                titles[username] = display
    finally:
        conn.close()
    return titles


def list_recent_wechat_sessions(config: AppConfig, days: int | None = None, db_root: Path | None = None) -> list[WeChatSession]:
    days = config.wechat.scan_days if days is None else days
    since_ts = int(datetime.now().timestamp()) - days * 86400

    snapshot_root = _copy_wechat_snapshot(config) if db_root is None else db_root
    contact_titles = _build_contact_titles(config, snapshot_root)
    path = _session_db_path(config, snapshot_root)
    if not path.exists():
        return []

    conn = sqlite3.connect(path)
    cur = conn.cursor()
    sessions: list[WeChatSession] = []
    seen_usernames: set[str] = set()
    try:
        rows = cur.execute(
            """
            select
              s.username,
              ifnull(n.session_title, ''),
              ifnull(s.last_timestamp, 0)
            from SessionTable s
            left join SessionNoContactInfoTable n on n.username = s.username
            where ifnull(s.last_timestamp, 0) >= ?
            order by s.last_timestamp desc
            """,
            (since_ts,),
        ).fetchall()

        fallback_rows: list[tuple[object, object, object]] = []
        allowlist = _normalized_session_allowlist(config)
        if allowlist:
            fallback_rows = cur.execute(
                """
                select
                  s.username,
                  ifnull(n.session_title, ''),
                  ifnull(s.last_timestamp, 0)
                from SessionTable s
                left join SessionNoContactInfoTable n on n.username = s.username
                """
            ).fetchall()
    finally:
        conn.close()

    for username, no_contact_title, last_timestamp in rows:
        _append_session_if_allowed(sessions, seen_usernames, config, contact_titles, username, no_contact_title, last_timestamp)

    for username, no_contact_title, last_timestamp in fallback_rows:
        _append_session_if_allowed(sessions, seen_usernames, config, contact_titles, username, no_contact_title, last_timestamp)

    return sessions[: config.wechat.max_sessions]


def _message_table_name(username: str) -> str:
    return "Msg_" + hashlib.md5(username.encode("utf-8")).hexdigest()


def _query_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "select 1 from sqlite_master where type='table' and name=? limit 1",
        (table_name,),
    ).fetchone()
    return row is not None


def _collect_session_lines(config: AppConfig, session: WeChatSession, since_ts: int, db_root: Path) -> tuple[list[str], int]:
    table_name = _message_table_name(session.username)
    lines: list[str] = []
    max_seen_ts = since_ts

    for db_path in _message_db_paths(config, db_root):
        conn = sqlite3.connect(db_path)
        conn.text_factory = bytes
        try:
            if not _query_table_exists(conn, table_name):
                continue
            rows = conn.execute(
                f"""
                select create_time, message_content
                from {table_name}
                where create_time >= ?
                  and message_content is not null
                order by create_time asc
                limit ?
                """,
                (
                    since_ts,
                    config.wechat.max_messages_per_session,
                ),
            ).fetchall()
        finally:
            conn.close()

        for create_time, message_content in rows:
            message_ts = int(create_time or 0)
            if message_ts > max_seen_ts:
                max_seen_ts = message_ts
            if not message_content:
                continue
            urls = _extract_urls_from_value(message_content)
            if not urls:
                continue
            timestamp = datetime.fromtimestamp(message_ts).strftime("%Y-%m-%d %H:%M:%S")
            text = _message_preview(message_content, urls)
            lines.append(f"[{timestamp}] {session.title}: {text}")
    return lines, max_seen_ts


def _collect_card_lines(snapshot_root: Path, config: AppConfig, since_ts: int) -> list[str]:
    helper_dir = config.project_root / "tools" / "wechat_card_scanner"
    if not helper_dir.exists():
        return []
    go_cache_dir = config.paths.runtime_dir / "go-cache"
    go_tmp_dir = config.paths.runtime_dir / "go-tmp"
    go_cache_dir.mkdir(parents=True, exist_ok=True)
    go_tmp_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "go",
        "run",
        ".",
        "--db-root",
        str(snapshot_root),
        "--since-ts",
        str(since_ts),
        "--max-sessions",
        str(config.wechat.max_sessions),
        "--max-messages-per-session",
        str(config.wechat.max_messages_per_session),
    ]
    command.append("--include-chatrooms=true" if config.wechat.include_chatrooms else "--include-chatrooms=false")
    if config.wechat.session_allowlist:
        command.extend(["--session-allowlist", ",".join(config.wechat.session_allowlist)])

    try:
        completed = subprocess.run(
            command,
            cwd=helper_dir,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={
                **dict(os.environ),
                "GOCACHE": str(go_cache_dir),
                "GOTMPDIR": str(go_tmp_dir),
            },
        )
    except Exception:
        return []

    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def collect_wechat_messages(
    config: AppConfig,
    report_date: date,
    days: int | None = None,
    force_full_scan: bool = False,
) -> CollectedInput | None:
    if not config.wechat.enabled:
        raise RuntimeError("WeChat collection is disabled.")

    # Refresh the exported WeChat workspace first when available so scheduled runs
    # can pick up newly received links without a separate manual refresh step.
    maybe_refresh_wechat_export(config)
    snapshot_root = _copy_wechat_snapshot(config)
    session_db = _session_db_path(config, snapshot_root)
    if not session_db.exists():
        raise RuntimeError(f"WeChat session database was not found: {session_db}")

    state = _load_state(config)
    default_since = int(datetime.now().timestamp()) - (days or config.wechat.scan_days) * 86400
    since_ts = default_since if force_full_scan else _load_last_scan_timestamp(config, state, default_since)

    sessions = list_recent_wechat_sessions(config, days=days, db_root=snapshot_root)
    lines: list[str] = []
    max_seen_ts = since_ts
    for session in sessions:
        session_lines, session_max_seen_ts = _collect_session_lines(config, session, since_ts, snapshot_root)
        if session_max_seen_ts > max_seen_ts:
            max_seen_ts = session_max_seen_ts
        lines.extend(session_lines)
    lines.extend(_collect_card_lines(snapshot_root, config, since_ts))

    deduped = list(dict.fromkeys(lines))
    _save_state(config, _build_scan_state(config, state, max_seen_ts))
    if not deduped:
        return None

    return store_text_input(config, "\n".join(deduped) + "\n", "wechat-auto", "wechat", report_date)
