from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
import shutil
import uuid

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
from app.models.note import NoteRecord
from app.services.note_records import note_record_path, save_note_record
from app.services.report_index import _dedupe_key, build_daily_report
from app.services.report_mutations import delete_failed_report_item, load_deleted_item_ids


def _build_config(root: Path) -> AppConfig:
    workspace_dir = root / "workspace"
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
            chatlog_root=root / "chatlog",
            account_dir="wxid_test",
            session_allowlist=["filehelper"],
            scan_days=3,
            include_chatrooms=False,
            max_sessions=20,
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
            provider_id="openai-compatible",
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


def _make_temp_root() -> Path:
    root = Path(__file__).resolve().parents[1] / ".tmp-tests"
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"report-mutations-{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_delete_failed_report_item_hides_item_and_clears_note_workspace() -> None:
    root = _make_temp_root()
    try:
        config = _build_config(root)
        report_date = date(2026, 4, 22)
        inbox = config.paths.inbox_dir / report_date.isoformat()
        inbox.mkdir(parents=True, exist_ok=True)

        source_url = "https://www.bilibili.com/video/BV1ab411c7mD/"
        item_id = hashlib.sha1(_dedupe_key(source_url).encode("utf-8")).hexdigest()[:16]
        (inbox / "101010-wechat-auto.txt").write_text(
            f"[2026-04-22 10:10:10] filehelper: {source_url}\n",
            encoding="utf-8",
        )
        save_note_record(
            config,
            NoteRecord(
                item_id=item_id,
                report_date=report_date.isoformat(),
                status="failed",
                source_url=source_url,
                source_title=source_url,
                source_context=source_url,
                source_origins=["wechat"],
                last_error="HTTP Error 412: Precondition Failed",
                last_error_code="bilibili_request_blocked",
                last_error_title="Request blocked",
                last_error_hint="Configure cookies and retry.",
            ),
        )

        assert build_daily_report(config, report_date).total_items == 1

        deleted = delete_failed_report_item(config, item_id, report_date)

        assert deleted is True
        assert item_id in load_deleted_item_ids(config, report_date)
        assert not note_record_path(config, item_id).exists()
        assert build_daily_report(config, report_date).total_items == 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_delete_failed_report_item_rejects_non_failed_status() -> None:
    root = _make_temp_root()
    try:
        config = _build_config(root)
        report_date = date(2026, 4, 22)
        inbox = config.paths.inbox_dir / report_date.isoformat()
        inbox.mkdir(parents=True, exist_ok=True)

        source_url = "https://www.bilibili.com/video/BV1ab411c7mD/"
        item_id = hashlib.sha1(_dedupe_key(source_url).encode("utf-8")).hexdigest()[:16]
        (inbox / "101010-wechat-auto.txt").write_text(
            f"[2026-04-22 10:10:10] filehelper: {source_url}\n",
            encoding="utf-8",
        )

        try:
            delete_failed_report_item(config, item_id, report_date)
        except RuntimeError as exc:
            assert str(exc) == "Only failed report items can be deleted from the card flow."
        else:
            raise AssertionError("Expected delete_failed_report_item to reject non-failed items.")
    finally:
        shutil.rmtree(root, ignore_errors=True)
