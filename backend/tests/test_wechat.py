from __future__ import annotations

import shutil
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

try:
    import zstandard as zstd
except ImportError:
    zstd = None

from app.config.settings import (
    AnalysisConfig,
    AppConfig,
    BilibiliConfig,
    ClipboardConfig,
    ModelProviderConfig,
    NotificationConfig,
    PathsConfig,
    RetentionConfig,
    ScheduleConfig,
    ServerConfig,
    TranscriberConfig,
    WeChatConfig,
)
from app.ingest.wechat import (
    _build_scan_state,
    _collect_session_lines,
    _copy_wechat_snapshot,
    _load_last_scan_timestamp,
    _message_db_paths,
    _message_table_name,
    WeChatSession,
    list_recent_wechat_sessions,
)
from app.ingest.wechat_paths import resolve_wechat_path


@contextmanager
def _test_root(name: str):
    root = Path.cwd() / ".tmp-tests" / name
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _build_config(root: Path, workspace_dir: Path, chatlog_root: Path) -> AppConfig:
    return AppConfig(
        project_root=root,
        paths=PathsConfig(
            workspace_dir=workspace_dir,
            inbox_dir=workspace_dir / "inbox",
            reports_dir=workspace_dir / "reports",
            runtime_dir=workspace_dir / "runtime",
        ),
        wechat=WeChatConfig(
            enabled=True,
            chatlog_root=chatlog_root,
            account_dir="wxid_test",
            session_allowlist=["filehelper"],
            scan_days=3,
            include_chatrooms=True,
            max_sessions=30,
            max_messages_per_session=80,
        ),
        clipboard=ClipboardConfig(enabled=True, include_on_schedule=False),
        bilibili=BilibiliConfig(cookies_file="", use_browser_cookies=False),
        schedule=ScheduleConfig(enabled=False, daily_time="21:00", auto_collect_wechat=True, notify_on_complete=True),
        retention=RetentionConfig(days=7, cleanup_intermediate=True),
        notification=NotificationConfig(enabled=True, open_target="daily_report"),
        server=ServerConfig(host="127.0.0.1", port=8765, open_browser=True, lan_enabled=True),
        analysis=AnalysisConfig(
            note_format="summary",
            note_style="detailed",
            enable_source_links=True,
            enable_mind_map=True,
            enable_ai_chat=True,
            enable_screenshots=False,
        ),
        transcriber=TranscriberConfig(
            type="openai_compatible",
            provider_id="openai",
            model_name="whisper-1",
            language="zh",
        ),
        providers=[
            ModelProviderConfig(
                provider_id="openai-compatible",
                label="OpenAI Compatible",
                base_url="https://api.openai.com/v1",
                api_key="",
                api_key_env="OPENAI_API_KEY",
                default_model="gpt-4.1-mini",
            )
        ],
    )


def test_message_table_name_uses_md5() -> None:
    assert _message_table_name("45402690906@chatroom") == "Msg_b662c35abe672b9cb6e9aa0929d15f7f"


def test_message_db_paths_include_biz_partitions() -> None:
    with _test_root("test_message_db_paths") as root:
        workspace_dir = root / "workspace"
        db_root = workspace_dir / "runtime" / "wechat_snapshot" / "wxid_test" / "db_storage"
        message_dir = db_root / "message"
        message_dir.mkdir(parents=True, exist_ok=True)
        for name in ("message_0.db", "biz_message_0.db", "message_resource.db"):
            (message_dir / name).write_bytes(b"")

        config = _build_config(root, workspace_dir, root / "chatlog")
        assert [path.name for path in _message_db_paths(config, db_root)] == ["biz_message_0.db", "message_0.db"]


def test_list_recent_wechat_sessions_honors_allowlist() -> None:
    with _test_root("test_session_allowlist") as root:
        workspace_dir = root / "workspace"
        db_root = workspace_dir / "runtime" / "wechat_snapshot" / "wxid_test" / "db_storage"
        contact_dir = db_root / "contact"
        session_dir = db_root / "session"
        contact_dir.mkdir(parents=True, exist_ok=True)
        session_dir.mkdir(parents=True, exist_ok=True)

        contact_conn = sqlite3.connect(contact_dir / "contact.db")
        contact_conn.execute("create table contact (username text, remark text, nick_name text)")
        contact_conn.execute("insert into contact values ('filehelper', '', '文件传输助手')")
        contact_conn.execute("insert into contact values ('friend_a', '', '朋友A')")
        contact_conn.commit()
        contact_conn.close()

        session_conn = sqlite3.connect(session_dir / "session.db")
        session_conn.execute("create table SessionTable (username text, last_timestamp integer)")
        session_conn.execute("create table SessionNoContactInfoTable (username text, session_title text)")
        session_conn.execute("insert into SessionTable values ('filehelper', 9999999999)")
        session_conn.execute("insert into SessionTable values ('friend_a', 9999999998)")
        session_conn.commit()
        session_conn.close()

        config = _build_config(root, workspace_dir, root / "chatlog")
        sessions = list_recent_wechat_sessions(config, days=3650, db_root=db_root)
        assert [session.username for session in sessions] == ["filehelper"]


def test_copy_wechat_snapshot_copies_companion_files() -> None:
    with _test_root("test_copy_snapshot") as root:
        workspace_dir = root / "workspace"
        chatlog_root = root / "chatlog"
        source_root = chatlog_root / "wxid_test" / "db_storage"
        files = [
            ("contact", "contact.db"),
            ("contact", "contact.db-wal"),
            ("session", "session.db"),
            ("session", "session.db-shm"),
            ("message", "message_0.db"),
            ("message", "message_0.db-wal"),
            ("message", "message_0.db-last.material"),
            ("message", "message_0.kvdb"),
        ]
        for subdir, name in files:
            path = source_root / subdir
            path.mkdir(parents=True, exist_ok=True)
            (path / name).write_bytes(name.encode("utf-8"))

        config = _build_config(root, workspace_dir, chatlog_root)
        resolved = _copy_wechat_snapshot(config)

        assert resolved == workspace_dir / "runtime" / "wechat_snapshot" / "wxid_test" / "db_storage"
        assert (resolved / "contact" / "contact.db-wal").exists()
        assert (resolved / "session" / "session.db-shm").exists()
        assert (resolved / "message" / "message_0.db-wal").exists()
        assert (resolved / "message" / "message_0.db-last.material").exists()
        assert (resolved / "message" / "message_0.kvdb").exists()


def test_resolve_wechat_path_uses_chatlog_history_when_settings_path_is_invalid() -> None:
    with _test_root("test_resolve_path") as root:
        workspace_dir = root / "workspace"
        invalid_chatlog_root = root / "chatlog"
        invalid_chatlog_root.write_text("not a directory", encoding="utf-8")

        work_dir = root / "Documents" / "chatlog" / "wxid_real"
        session_dir = work_dir / "db_storage" / "session"
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "session.db").write_bytes(b"")

        chatlog_config_dir = root / ".chatlog"
        chatlog_config_dir.mkdir(parents=True, exist_ok=True)
        (chatlog_config_dir / "chatlog.json").write_text(
            """
            {
              "history": [
                {
                  "type": "wechat",
                  "account": "wxid_real",
                  "platform": "windows",
                  "version": 4,
                  "data_dir": "C:\\\\data",
                  "data_key": "abc",
                  "work_dir": "__WORK_DIR__"
                }
              ],
              "last_account": "wxid_real"
            }
            """.replace("__WORK_DIR__", str(work_dir).replace("\\", "\\\\")),
            encoding="utf-8",
        )

        config = _build_config(root, workspace_dir, invalid_chatlog_root)
        config.wechat.account_dir = ""

        with patch("app.ingest.wechat_paths.Path.home", return_value=root):
            resolved = resolve_wechat_path(config)

        assert resolved is not None
        assert resolved.account == "wxid_real"
        assert resolved.account_root == work_dir
        assert resolved.db_root == work_dir / "db_storage"
        assert resolved.source == "chatlog-history"


def test_collect_session_lines_extracts_urls_from_bytes_and_tracks_message_timestamp() -> None:
    with _test_root("test_collect_session_lines") as root:
        workspace_dir = root / "workspace"
        db_root = workspace_dir / "runtime" / "wechat_snapshot" / "wxid_test" / "db_storage"
        message_dir = db_root / "message"
        message_dir.mkdir(parents=True, exist_ok=True)

        config = _build_config(root, workspace_dir, root / "chatlog")
        table_name = _message_table_name("filehelper")
        message_db = sqlite3.connect(message_dir / "message_0.db")
        message_db.execute(f"create table {table_name} (create_time integer, message_content blob)")
        message_db.execute(
            f"insert into {table_name} values (?, ?)",
            (200, sqlite3.Binary(b"\x00\x10https://example.com/report?id=1\x00")),
        )
        message_db.execute(
            f"insert into {table_name} values (?, ?)",
            (260, sqlite3.Binary("日报链接 https://example.com/daily".encode("utf-8"))),
        )
        message_db.commit()
        message_db.close()

        session = WeChatSession(username="filehelper", title="文件传输助手", last_timestamp=999, is_chatroom=False)
        lines, max_seen_ts = _collect_session_lines(config, session, since_ts=100, db_root=db_root)

        assert max_seen_ts == 260
        assert len(lines) == 2
        assert "https://example.com/report?id=1" in lines[0]
        assert "https://example.com/daily" in lines[1]
        assert "日报链接" in lines[1]


def test_collect_session_lines_extracts_urls_from_zstd_xml_messages() -> None:
    if zstd is None:
        return

    with _test_root("test_collect_session_lines_zstd") as root:
        workspace_dir = root / "workspace"
        db_root = workspace_dir / "runtime" / "wechat_snapshot" / "wxid_test" / "db_storage"
        message_dir = db_root / "message"
        message_dir.mkdir(parents=True, exist_ok=True)

        config = _build_config(root, workspace_dir, root / "chatlog")
        table_name = _message_table_name("filehelper")
        payload = (
            "<?xml version='1.0'?><msg><appmsg><title>Example Share</title>"
            "<des>Example Desc</des><url>https://example.com/share</url></appmsg>"
            "<appinfo><appname>Example App</appname></appinfo></msg>"
        ).encode("utf-8")
        compressed = zstd.ZstdCompressor().compress(payload)

        message_db = sqlite3.connect(message_dir / "message_0.db")
        message_db.execute(f"create table {table_name} (create_time integer, message_content blob)")
        message_db.execute(f"insert into {table_name} values (?, ?)", (300, sqlite3.Binary(compressed)))
        message_db.commit()
        message_db.close()

        session = WeChatSession(username="filehelper", title="鏂囦欢浼犺緭鍔╂墜", last_timestamp=999, is_chatroom=False)
        lines, max_seen_ts = _collect_session_lines(config, session, since_ts=100, db_root=db_root)

        assert max_seen_ts == 300
        assert len(lines) == 1
        assert "https://example.com/share" in lines[0]
        assert "Example Share" in lines[0]
        assert "<?xml" not in lines[0]


def test_scan_state_is_tracked_per_account() -> None:
    with _test_root("test_scan_state") as root:
        workspace_dir = root / "workspace"
        chatlog_root = root / "chatlog"
        config = _build_config(root, workspace_dir, chatlog_root)
        default_since = 123

        state = _build_scan_state(config, {}, 456)

        assert state["last_scan_timestamp"] == 456
        assert _load_last_scan_timestamp(config, state, default_since) == 456
        assert isinstance(state["last_scan_by_account"], dict)
        assert len(state["last_scan_by_account"]) == 1
