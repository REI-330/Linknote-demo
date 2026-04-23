from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

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
    load_config,
)
from app.services.config_manager import save_app_config
from app.services.diagnostics import _resolve_active_provider
from app.services.provider_catalog import add_enabled_model, resolve_analysis_target, test_provider_connection


def _build_config() -> AppConfig:
    root = Path(__file__).resolve().parents[1] / ".tmp-tests" / "provider-catalog"
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
        ),
        transcriber=TranscriberConfig(
            type="faster_whisper",
            provider_id="gemini-openai",
            model_name="small",
            language="zh",
        ),
        providers=[
            ModelProviderConfig(
                provider_id="gemini-openai",
                label="Gemini OpenAI Compatible",
                base_url="https://generativelanguage.googleapis.com/v1beta/openai",
                api_key="",
                api_key_env="GEMINI_API_KEY",
                default_model="",
                models=[],
                enabled=True,
            ),
            ModelProviderConfig(
                provider_id="openai-compatible",
                label="OpenAI Compatible",
                base_url="https://api.openai.com/v1",
                api_key="",
                api_key_env="OPENAI_API_KEY",
                default_model="gpt-4.1-mini",
                models=["gpt-4.1-mini"],
                enabled=True,
            ),
        ],
    )


class ResolveAnalysisTargetTests(unittest.TestCase):
    def test_default_selection_ignores_transcriber_provider_without_models(self) -> None:
        config = _build_config()

        provider, model_name = resolve_analysis_target(config)

        self.assertEqual(provider.provider_id, "openai-compatible")
        self.assertEqual(model_name, "gpt-4.1-mini")

    def test_health_resolution_follows_analysis_target_not_transcriber_provider(self) -> None:
        config = _build_config()

        provider = _resolve_active_provider(config)

        self.assertIsNotNone(provider)
        self.assertEqual(provider.provider_id, "openai-compatible")


class BuiltinProviderMergeTests(unittest.TestCase):
    def test_load_config_merges_bilinote_builtin_providers(self) -> None:
        config = _build_config()
        save_app_config(config)

        loaded = load_config(config.project_root)
        provider_ids = [provider.provider_id for provider in loaded.providers]

        self.assertEqual(
            provider_ids[:7],
            ["openai", "deepseek", "qwen", "Claude", "gemini", "groq", "ollama"],
        )

        openai = next(provider for provider in loaded.providers if provider.provider_id == "openai")
        self.assertEqual(openai.label, "OpenAI")
        self.assertEqual(openai.logo, "OpenAI")
        self.assertEqual(openai.type, "built-in")

        custom = next(provider for provider in loaded.providers if provider.provider_id == "openai-compatible")
        self.assertEqual(custom.label, "OpenAI Compatible")
        self.assertEqual(custom.logo, "custom")
        self.assertEqual(custom.type, "custom")

    def test_load_config_repairs_root_only_builtin_base_url(self) -> None:
        config = _build_config()
        config.providers.append(
            ModelProviderConfig(
                provider_id="gemini",
                label="Gemini",
                base_url="https://generativelanguage.googleapis.com",
                api_key="test-key",
                api_key_env="",
                default_model="models/gemini-2.5-flash",
                models=["models/gemini-2.5-flash"],
                enabled=True,
            )
        )
        save_app_config(config)

        loaded = load_config(config.project_root)
        gemini = next(provider for provider in loaded.providers if provider.provider_id == "gemini")

        self.assertEqual(gemini.base_url, "https://generativelanguage.googleapis.com/v1beta/openai")

    def test_requested_model_name_can_pick_matching_enabled_provider(self) -> None:
        config = _build_config()

        provider, model_name = resolve_analysis_target(config, model_name="gpt-4.1-mini")

        self.assertEqual(provider.provider_id, "openai-compatible")
        self.assertEqual(model_name, "gpt-4.1-mini")

    def test_provider_connection_raises_runtime_error_with_provider_context(self) -> None:
        config = _build_config()
        config.providers[1] = replace(config.providers[1], api_key="test-key")
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("404 not found")

        with patch("app.services.provider_catalog.OpenAI", return_value=mock_client):
            with self.assertRaisesRegex(RuntimeError, "OpenAI Compatible: 404 not found"):
                test_provider_connection(config, "openai-compatible")

    def test_add_enabled_model_rejects_duplicate_with_clear_reason(self) -> None:
        config = _build_config()

        with self.assertRaisesRegex(RuntimeError, "OpenAI Compatible: model is already enabled."):
            add_enabled_model(config, "openai-compatible", "gpt-4.1-mini")


if __name__ == "__main__":
    unittest.main()
