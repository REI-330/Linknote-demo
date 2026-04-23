from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from app.config.settings import (
    AnalysisConfig,
    AppConfig,
    ClipboardConfig,
    ModelProviderConfig,
    NotificationConfig,
    PathsConfig,
    RetentionConfig,
    ScheduleConfig,
    ServerConfig,
    WeChatConfig,
)
from app.models.note import NoteRecord
from app.services.note_records import append_note_version, load_note_record, save_note_record


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
        wechat=WeChatConfig(True, root / "chatlog", "wxid_test", ["filehelper"], 3, False, 20, 80),
        clipboard=ClipboardConfig(True, False),
        schedule=ScheduleConfig(False, "21:00", True, True),
        retention=RetentionConfig(7, True),
        notification=NotificationConfig(True, "daily_report"),
        server=ServerConfig("127.0.0.1", 8765, True, True),
        analysis=AnalysisConfig("summary", "detailed", True, True, True, False),
        providers=[
            ModelProviderConfig(
                provider_id="openai-compatible",
                label="OpenAI Compatible",
                base_url="https://api.openai.com/v1",
                api_key_env="OPENAI_API_KEY",
                default_model="gpt-4.1-mini",
            )
        ],
    )


def test_append_note_version_persists_record() -> None:
    with TemporaryDirectory(dir=r"C:\Users\hr206\linknote") as tmp:
        root = Path(tmp)
        config = _build_config(root)
        record = NoteRecord(
            item_id="item-123",
            report_date="2026-04-18",
            status="pending",
            source_url="https://www.bilibili.com/video/BV1ab411c7mD/",
            source_title="测试视频",
            source_context="原始上下文",
            source_origins=["wechat"],
        )
        save_note_record(config, record)
        append_note_version(
            config,
            record,
            label="版本 1",
            markdown="# 测试",
            source_basis="metadata_only",
            model_name="preview",
            provider_id="internal",
        )

        loaded = load_note_record(config, "item-123")
        assert loaded is not None
        assert loaded.status == "completed"
        assert len(loaded.versions) == 1
        assert loaded.versions[0].markdown == "# 测试"

