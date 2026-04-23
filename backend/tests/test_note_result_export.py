from __future__ import annotations

import json
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
from app.models.media import MediaDownloadResult, TranscriptResult, TranscriptSegmentResult
from app.models.note import NoteRecord, NoteVersion, TranscriptSegment
from app.services.note_result_export import ensure_note_result_snapshot, note_result_path, write_bilinote_note_result


def _build_config(root: Path, workspace_dir: Path | None = None) -> AppConfig:
    workspace_dir = workspace_dir or (root / "workspace")
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
        bilibili=BilibiliConfig("", False),
        schedule=ScheduleConfig(False, "21:00", True, True),
        retention=RetentionConfig(7, True),
        notification=NotificationConfig(True, "daily_report"),
        server=ServerConfig("127.0.0.1", 8765, True, True),
        analysis=AnalysisConfig("summary", "detailed", True, True, True, False),
        transcriber=TranscriberConfig("openai_compatible", "openai-compatible", "whisper-1", "zh"),
        providers=[
            ModelProviderConfig(
                provider_id="openai-compatible",
                label="OpenAI Compatible",
                base_url="https://api.openai.com/v1",
                api_key="",
                api_key_env="OPENAI_API_KEY",
                default_model="gpt-4.1-mini",
                enabled=True,
            )
        ],
    )


def test_write_bilinote_note_result_exports_compatible_shape() -> None:
    root = Path(r"C:\Users\hr206\linknote")
    workspace_dir = root / "backend" / ".tmp-tests"
    config = _build_config(root, workspace_dir)
    record = NoteRecord(
        item_id="item-1",
        report_date="2026-04-19",
        status="completed",
        source_url="https://www.bilibili.com/video/BV1xx411c7mD/",
        source_title="测试视频",
        source_context="测试上下文",
        source_origins=["wechat"],
    )
    media = MediaDownloadResult(
        source_url=record.source_url,
        canonical_url="https://www.bilibili.com/video/BV1xx411c7mD?p=2",
        platform="bilibili",
        video_id="BV1xx411c7mD",
        title="测试视频",
        duration=128.0,
        cover_url="https://example.com/cover.jpg",
        description="一段测试简介",
        uploader="tester",
        tags=["检索增强", "问答"],
        audio_path="audio.m4a",
        video_path="video.mp4",
        raw_info={},
    )
    transcript = TranscriptResult(
        language="zh",
        full_text="这里提到检索增强。",
        segments=[TranscriptSegmentResult(start=12.0, end=18.0, text="这里提到检索增强。")],
    )

    output_path = write_bilinote_note_result(
        config,
        record,
        media=media,
        transcript=transcript,
        markdown="## 测试\n这里是生成的笔记。",
    )

    assert output_path == note_result_path(config, "item-1")
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["markdown"].startswith("## 测试")
    assert payload["transcript"]["segments"][0]["text"] == "这里提到检索增强。"
    assert payload["audio_meta"]["title"] == "测试视频"
    assert payload["audio_meta"]["raw_info"]["webpage_url"] == "https://www.bilibili.com/video/BV1xx411c7mD?p=2"


def test_ensure_note_result_snapshot_uses_existing_record_content() -> None:
    root = Path(r"C:\Users\hr206\linknote")
    workspace_dir = root / "backend" / ".tmp-tests"
    config = _build_config(root, workspace_dir)
    record = NoteRecord(
        item_id="item-2",
        report_date="2026-04-19",
        status="completed",
        source_url="https://www.bilibili.com/video/BV1yy411c7mD/",
        source_title="已分析视频",
        source_context="测试上下文",
        source_origins=["wechat"],
        transcript_segments=[TranscriptSegment(start=3.0, end=8.0, text="这里解释来源卡片。")],
        metadata={
            "canonical_url": "https://www.bilibili.com/video/BV1yy411c7mD?p=3",
            "platform": "bilibili",
            "video_id": "BV1yy411c7mD",
            "duration": 66,
            "description": "已有 note 记录",
            "uploader": "tester",
            "tags": ["来源卡片"],
            "raw_info": {"view_count": 1234},
        },
        versions=[
            NoteVersion(
                version_id="v1",
                label="分析版本 1",
                markdown="## 来源卡片\n这里已经有现成笔记。",
                source_basis="platform_subtitle",
                created_at="2026-04-19 10:00:00",
            )
        ],
    )

    output_path = ensure_note_result_snapshot(config, record)

    assert output_path == note_result_path(config, "item-2")
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["markdown"] == "## 来源卡片\n这里已经有现成笔记。"
    assert payload["transcript"]["segments"][0]["text"] == "这里解释来源卡片。"
    assert payload["audio_meta"]["video_id"] == "BV1yy411c7mD"
