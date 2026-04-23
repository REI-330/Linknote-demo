from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..config.settings import AppConfig


@dataclass(slots=True)
class ChatlogHistoryEntry:
    account: str
    platform: str
    version: int
    data_dir: Path
    work_dir: Path
    data_key: str


@dataclass(slots=True)
class ResolvedWeChatPath:
    account: str
    account_root: Path
    db_root: Path
    source: str


@dataclass(slots=True)
class WeChatAccountOption:
    account: str
    chatlog_root: Path
    label: str


def chatlog_config_path() -> Path:
    return Path.home() / ".chatlog" / "chatlog.json"


def load_chatlog_history_entry(config: AppConfig) -> ChatlogHistoryEntry:
    entry = find_chatlog_history_entry(config)
    if entry is None:
        account = config.wechat.account_dir.strip() or _last_chatlog_account() or "<unknown>"
        raise RuntimeError(f"chatlog.json does not contain WeChat account {account}.")
    if not entry.data_key or entry.version <= 0:
        raise RuntimeError("chatlog history entry is incomplete.")
    return entry


def find_chatlog_history_entry(config: AppConfig) -> ChatlogHistoryEntry | None:
    config_path = chatlog_config_path()
    if not config_path.exists():
        return None

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    entries = _load_chatlog_history_entries(raw)
    if not entries:
        return None

    preferred_accounts: list[str] = []
    configured_account = config.wechat.account_dir.strip()
    if configured_account:
        preferred_accounts.append(configured_account)
    last_account = str(raw.get("last_account") or "").strip()
    if last_account and last_account not in preferred_accounts:
        preferred_accounts.append(last_account)

    for account in preferred_accounts:
        matched = next((entry for entry in entries if entry.account == account), None)
        if matched is not None:
            return matched

    configured_root = config.wechat.chatlog_root
    for entry in entries:
        if configured_root == entry.work_dir or configured_root == entry.work_dir.parent:
            return entry

    return entries[0]


def list_wechat_account_options(config: AppConfig) -> list[WeChatAccountOption]:
    options: list[WeChatAccountOption] = []
    seen: set[tuple[str, str]] = set()

    history_entries = _load_chatlog_history_entries_from_file()
    for entry in history_entries:
        key = (entry.account, str(entry.work_dir.parent))
        if key in seen:
            continue
        options.append(
            WeChatAccountOption(
                account=entry.account,
                chatlog_root=entry.work_dir.parent,
                label=entry.account,
            )
        )
        seen.add(key)

    configured_account = config.wechat.account_dir.strip()
    configured_root = config.wechat.chatlog_root
    if configured_account and configured_root.exists():
        key = (configured_account, str(configured_root))
        if key not in seen:
            options.append(
                WeChatAccountOption(
                    account=configured_account,
                    chatlog_root=configured_root,
                    label=configured_account,
                )
            )
    return options


def resolve_wechat_path(config: AppConfig) -> ResolvedWeChatPath | None:
    configured_root = config.wechat.chatlog_root
    configured_account = config.wechat.account_dir.strip()

    direct_candidates: list[tuple[Path, str, str]] = []
    if configured_account:
        direct_candidates.append((configured_root / configured_account, configured_account, "settings"))
    direct_candidates.append((configured_root, configured_account, "settings"))

    for candidate_root, candidate_account, source in direct_candidates:
        db_root = _resolve_db_root(candidate_root)
        if db_root is None:
            continue
        return ResolvedWeChatPath(
            account=candidate_account or _account_name_from_db_root(db_root),
            account_root=_account_root_from_db_root(db_root),
            db_root=db_root,
            source=source,
        )

    if configured_root.exists() and configured_root.is_dir():
        child_roots = [
            child
            for child in sorted(configured_root.iterdir())
            if child.is_dir() and _resolve_db_root(child) is not None
        ]
        if child_roots:
            matched_child = None
            history_entry = find_chatlog_history_entry(config)
            if history_entry is not None:
                matched_child = next((child for child in child_roots if child.name == history_entry.account), None)
            if matched_child is None and len(child_roots) == 1:
                matched_child = child_roots[0]
            if matched_child is not None:
                db_root = _resolve_db_root(matched_child)
                if db_root is not None:
                    return ResolvedWeChatPath(
                        account=matched_child.name,
                        account_root=matched_child,
                        db_root=db_root,
                        source="settings-auto",
                    )

    history_entry = find_chatlog_history_entry(config)
    if history_entry is None:
        return None
    history_db_root = _resolve_db_root(history_entry.work_dir)
    if history_db_root is None:
        return None
    return ResolvedWeChatPath(
        account=history_entry.account,
        account_root=history_entry.work_dir,
        db_root=history_db_root,
        source="chatlog-history",
    )


def describe_wechat_path(config: AppConfig) -> str:
    resolved = resolve_wechat_path(config)
    if resolved is not None:
        return f"{resolved.db_root / 'session' / 'session.db'} ({resolved.source})"

    configured_root = config.wechat.chatlog_root
    configured_account = config.wechat.account_dir.strip()
    if configured_account:
        return str(configured_root / configured_account / "db_storage" / "session" / "session.db")
    return str(configured_root / "db_storage" / "session" / "session.db")


def _parse_history_entry(item: object) -> ChatlogHistoryEntry | None:
    if not isinstance(item, dict):
        return None
    if str(item.get("type") or "").strip().lower() != "wechat":
        return None

    account = str(item.get("account") or "").strip()
    work_dir_raw = str(item.get("work_dir") or "").strip()
    if not account or not work_dir_raw:
        return None

    data_dir_raw = str(item.get("data_dir") or "").strip()
    version_raw = item.get("version")
    try:
        version = int(version_raw or 0)
    except (TypeError, ValueError):
        version = 0

    return ChatlogHistoryEntry(
        account=account,
        platform=str(item.get("platform") or "").strip() or "windows",
        version=version,
        data_dir=Path(data_dir_raw).expanduser() if data_dir_raw else Path(),
        work_dir=Path(work_dir_raw).expanduser(),
        data_key=str(item.get("data_key") or "").strip(),
    )


def _last_chatlog_account() -> str:
    config_path = chatlog_config_path()
    if not config_path.exists():
        return ""
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return str(raw.get("last_account") or "").strip()


def _load_chatlog_history_entries_from_file() -> list[ChatlogHistoryEntry]:
    config_path = chatlog_config_path()
    if not config_path.exists():
        return []
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return _load_chatlog_history_entries(raw)


def _load_chatlog_history_entries(raw: object) -> list[ChatlogHistoryEntry]:
    if not isinstance(raw, dict):
        return []
    history = raw.get("history", [])
    if not isinstance(history, list):
        raise RuntimeError("chatlog.json is invalid: history must be a list.")
    return [entry for entry in (_parse_history_entry(item) for item in history) if entry is not None]


def _resolve_db_root(candidate_root: Path) -> Path | None:
    if not candidate_root.exists() or not candidate_root.is_dir():
        return None
    direct_db_root = candidate_root / "db_storage"
    if _session_db_exists(direct_db_root):
        return direct_db_root
    if _session_db_exists(candidate_root):
        return candidate_root
    return None


def _session_db_exists(db_root: Path) -> bool:
    return (db_root / "session" / "session.db").exists()


def _account_root_from_db_root(db_root: Path) -> Path:
    return db_root.parent if db_root.name == "db_storage" else db_root


def _account_name_from_db_root(db_root: Path) -> str:
    account_root = _account_root_from_db_root(db_root)
    return account_root.name if account_root.name else "default"
