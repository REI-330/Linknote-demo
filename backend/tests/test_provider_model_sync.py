from __future__ import annotations

import unittest
from pathlib import Path

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
from app.services.provider_catalog import delete_enabled_model, update_provider


def _build_config() -> AppConfig:
    root = Path(__file__).resolve().parents[1] / ".tmp-tests" / "provider-model-sync"
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
            account_dir="",
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
            provider_id="gemini-openai",
            model_name="models/gemini-2.5-flash",
        ),
        transcriber=TranscriberConfig(
            type="faster_whisper",
            provider_id="openai",
            model_name="small",
            language="zh",
        ),
        providers=[
            ModelProviderConfig(
                provider_id="gemini-openai",
                label="Gemini OpenAI Compatible",
                base_url="https://generativelanguage.googleapis.com/v1beta/openai",
                api_key="test-key",
                api_key_env="",
                default_model="models/gemini-2.5-flash",
                models=["models/gemini-2.5-flash"],
                enabled=True,
            )
        ],
    )


class ProviderModelSyncTests(unittest.TestCase):
    def test_update_provider_clears_stale_models_when_custom_base_url_changes(self) -> None:
        config = _build_config()

        update_provider(
            config,
            "gemini-openai",
            {
                "name": "deepseek relay",
                "base_url": "https://xh.v1api.cc/v1",
                "api_key": "relay-key",
                "enabled": True,
            },
        )

        provider = config.providers[0]
        self.assertEqual(provider.base_url, "https://xh.v1api.cc/v1")
        self.assertEqual(provider.default_model, "")
        self.assertEqual(provider.models, [])
        self.assertEqual(config.analysis.provider_id, "")
        self.assertEqual(config.analysis.model_name, "")

    def test_delete_enabled_model_clears_selected_analysis_target(self) -> None:
        config = _build_config()

        removed = delete_enabled_model(config, "gemini-openai:models/gemini-2.5-flash")

        self.assertTrue(removed)
        provider = config.providers[0]
        self.assertEqual(provider.default_model, "")
        self.assertEqual(provider.models, [])
        self.assertEqual(config.analysis.provider_id, "")
        self.assertEqual(config.analysis.model_name, "")


if __name__ == "__main__":
    unittest.main()
