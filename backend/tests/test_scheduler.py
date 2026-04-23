from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

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
from app.services.daily_runner import _save_runner_state
from app.services.scheduler import _should_run_now, next_run_at


def _build_config(root: Path, workspace_dir: Path) -> AppConfig:
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
            account_dir="",
            session_allowlist=["filehelper"],
            scan_days=3,
            include_chatrooms=False,
            max_sessions=20,
            max_messages_per_session=80,
        ),
        clipboard=ClipboardConfig(enabled=True, include_on_schedule=True),
        bilibili=BilibiliConfig(cookies_file="", use_browser_cookies=False),
        schedule=ScheduleConfig(enabled=True, daily_time="21:00", auto_collect_wechat=True, notify_on_complete=True),
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
        transcriber=TranscriberConfig(type="openai_compatible", provider_id="openai", model_name="whisper-1", language="zh"),
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


def test_next_run_at_rolls_to_next_day_after_cutoff() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = _build_config(root, root / "workspace")

        assert next_run_at(config, now=datetime(2026, 4, 21, 20, 30, 0)) == "2026-04-21 21:00:00"
        assert next_run_at(config, now=datetime(2026, 4, 21, 21, 0, 0)) == "2026-04-22 21:00:00"


def test_should_run_now_allows_catch_up_after_target_time() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = _build_config(root, root / "workspace")
        _save_runner_state(
            config,
            {
                "last_reason": "manual",
                "last_report_date": "2026-04-20",
            },
        )

        class FakeDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 4, 21, 21, 35, 0)

            @classmethod
            def strptime(cls, date_string, fmt):
                return datetime.strptime(date_string, fmt)

        import app.services.scheduler as scheduler_module

        original_datetime = scheduler_module.datetime
        try:
            scheduler_module.datetime = FakeDateTime
            assert _should_run_now(config) is True
        finally:
            scheduler_module.datetime = original_datetime
