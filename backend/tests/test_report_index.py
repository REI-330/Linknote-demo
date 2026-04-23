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
from app.services.note_records import save_note_record
from app.services.report_index import _dedupe_key, build_daily_report, note_detail_stub


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
    target = root / f"report-index-{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_dedupe_key_prefers_bvid() -> None:
    assert _dedupe_key("https://www.bilibili.com/video/BV1ab411c7mD/?spm_id_from=333.1007.tianma.1-1-1.click") == "bvid:BV1AB411C7MD"


def test_build_daily_report_merges_origins_for_same_link() -> None:
    root = _make_temp_root()
    try:
        config = _build_config(root)
        report_date = date(2026, 4, 18)
        inbox = config.paths.inbox_dir / report_date.isoformat()
        inbox.mkdir(parents=True, exist_ok=True)

        (inbox / "101010-wechat-auto.txt").write_text(
            "[2026-04-18 10:10:10] 文件传输助手: 这个视频不错 https://www.bilibili.com/video/BV1ab411c7mD/?spm_id_from=333.1007.tianma.1-1-1.click\n",
            encoding="utf-8",
        )
        (inbox / "101011-clipboard.txt").write_text(
            "https://www.bilibili.com/video/BV1ab411c7mD/\n",
            encoding="utf-8",
        )

        report = build_daily_report(config, report_date)
        assert report.total_items == 1
        assert report.items[0].source_origins == ["clipboard", "wechat"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_build_daily_report_normalizes_non_bvid_urls() -> None:
    root = _make_temp_root()
    try:
        config = _build_config(root)
        report_date = date(2026, 4, 18)
        inbox = config.paths.inbox_dir / report_date.isoformat()
        inbox.mkdir(parents=True, exist_ok=True)

        (inbox / "101010-manual.txt").write_text(
            "https://example.com/watch?v=123&utm_source=abc\n",
            encoding="utf-8",
        )
        (inbox / "101011-clipboard.txt").write_text(
            "https://example.com/watch?v=123\n",
            encoding="utf-8",
        )

        report = build_daily_report(config, report_date)
        assert report.total_items == 1
        assert report.items[0].source_origins == ["clipboard", "manual"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_build_daily_report_exposes_failure_summary() -> None:
    root = _make_temp_root()
    try:
        config = _build_config(root)
        report_date = date(2026, 4, 18)
        inbox = config.paths.inbox_dir / report_date.isoformat()
        inbox.mkdir(parents=True, exist_ok=True)

        source_url = "https://www.bilibili.com/video/BV1ab411c7mD/"
        item_id = hashlib.sha1(_dedupe_key(source_url).encode("utf-8")).hexdigest()[:16]
        (inbox / "101010-wechat-auto.txt").write_text(
            f"[2026-04-18 10:10:10] filehelper: {source_url}\n",
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
                last_error="No usable Bilibili cookie source was available.",
                last_error_code="bilibili_cookies_required",
                last_error_title="Cookies required",
                last_error_hint="Configure cookies.txt first.",
            ),
        )

        report = build_daily_report(config, report_date)
        assert report.total_items == 1
        assert report.items[0].status == "failed"
        assert report.items[0].failure_code == "bilibili_cookies_required"
        assert report.items[0].failure_title == "Cookies required"
        assert report.items[0].failure_hint == "Configure cookies.txt first."
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_note_detail_stub_exposes_actions_for_blocked_requests() -> None:
    root = _make_temp_root()
    try:
        config = _build_config(root)
        report_date = date(2026, 4, 18)
        inbox = config.paths.inbox_dir / report_date.isoformat()
        inbox.mkdir(parents=True, exist_ok=True)

        source_url = "https://www.bilibili.com/video/BV1ab411c7mD/"
        item_id = hashlib.sha1(_dedupe_key(source_url).encode("utf-8")).hexdigest()[:16]
        (inbox / "101010-wechat-auto.txt").write_text(
            f"[2026-04-18 10:10:10] filehelper: {source_url}\n",
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
                last_error_title="B站拒绝了当前请求",
                last_error_hint="改用标准 BV 链接或配置 cookies 后重试。",
            ),
        )

        detail = note_detail_stub(config, item_id, report_date)
        assert detail["analysis"]["failure"]["actions"] == ["settings", "retry", "source"]
    finally:
        shutil.rmtree(root, ignore_errors=True)
