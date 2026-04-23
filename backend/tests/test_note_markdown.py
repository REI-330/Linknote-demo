from __future__ import annotations

import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

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
from app.models.media import MediaDownloadResult
from app.services.note_generation import _post_process_markdown
from app.services.note_markdown import extract_screenshot_timestamps, insert_screenshots, replace_content_markers


@contextmanager
def _controlled_temp_dir() -> Path:
    root = Path(__file__).resolve().parents[1] / ".test-temp" / uuid.uuid4().hex[:8]
    root.mkdir(parents=True, exist_ok=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


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
            enable_screenshots=True,
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
                enabled=True,
            )
        ],
    )


def test_extract_screenshot_timestamps_supports_both_marker_styles() -> None:
    markdown = "*Screenshot-[01:02]\n正文\nScreenshot-03:04"
    assert extract_screenshot_timestamps(markdown) == [
        ("*Screenshot-[01:02]", 62),
        ("Screenshot-03:04", 184),
    ]


def test_replace_content_markers_preserves_existing_query_params() -> None:
    markdown = "## 标题 *Content-[01:02]"
    replaced = replace_content_markers(markdown, "https://www.bilibili.com/video/BV1xx411c7mD?p=2")
    assert replaced == "## 标题 [原片 @ 01:02](https://www.bilibili.com/video/BV1xx411c7mD?p=2&t=62)"


def test_insert_screenshots_replaces_markers_with_image_urls() -> None:
    with _controlled_temp_dir() as root:
        output_dir = root / "screenshots"
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / "mock-shot.jpg"
        image_path.write_bytes(b"jpg")

        with patch("app.services.note_markdown.generate_screenshot", return_value=image_path):
            rendered = insert_screenshots(
                "段落\n*Screenshot-[00:06]",
                video_path="demo.mp4",
                output_dir=output_dir,
            )

        assert rendered == "段落\n![](/static/screenshots/mock-shot.jpg)"


def test_post_process_markdown_inserts_screenshots_links_and_source_header() -> None:
    with _controlled_temp_dir() as root:
        config = _build_config(root)
        media = MediaDownloadResult(
            source_url="https://www.bilibili.com/video/BV1xx411c7mD?p=2",
            canonical_url="https://www.bilibili.com/video/BV1xx411c7mD?p=2",
            platform="bilibili",
            video_id="BV1xx411c7mD",
            title="测试视频",
            duration=10.0,
            cover_url="",
            description="",
            uploader="",
            tags=[],
            audio_path="audio.m4a",
            video_path="video.mp4",
            raw_info={},
        )

        with patch(
            "app.services.note_generation.insert_screenshots",
            return_value="## 标题 *Content-[00:06]\n![](/static/screenshots/demo.jpg)",
        ):
            rendered = _post_process_markdown(
                config,
                "## 标题 *Content-[00:06]\n*Screenshot-[00:06]",
                media,
                media.source_url,
            )

        assert rendered.startswith("> 来源链接：https://www.bilibili.com/video/BV1xx411c7mD?p=2\n\n")
        assert "[原片 @ 00:06](https://www.bilibili.com/video/BV1xx411c7mD?p=2&t=6)" in rendered
        assert "![](/static/screenshots/demo.jpg)" in rendered
