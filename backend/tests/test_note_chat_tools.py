from __future__ import annotations

import json

from app.models.note import NoteRecord, NoteVersion, TranscriptSegment
from app.services.note_chat_tools import execute_tool


def _build_record() -> NoteRecord:
    return NoteRecord(
        item_id="item-1",
        report_date="2026-04-19",
        status="completed",
        source_url="https://www.bilibili.com/video/BV1xx411c7mD/",
        source_title="测试视频",
        source_context="测试上下文",
        source_origins=["wechat"],
        transcript_segments=[
            TranscriptSegment(start=5, end=11, text="第一段提到转录查询。"),
            TranscriptSegment(start=12, end=20, text="第二段提到工具调用和全文检索。"),
            TranscriptSegment(start=21, end=28, text="第三段说明为什么要保留完整笔记。"),
        ],
        metadata={
            "canonical_url": "https://www.bilibili.com/video/BV1xx411c7mD?p=2",
            "uploader": "tester",
            "description": "这是一段用于工具调用测试的简介",
            "tags": ["工具调用", "问答"],
            "duration": 180,
            "platform": "bilibili",
            "video_id": "BV1xx411c7mD",
        },
        versions=[
            NoteVersion(
                version_id="v1",
                label="分析版本 1",
                markdown="## 工具调用\n这里保留完整笔记内容，供 get_note_content 调用。",
                source_basis="platform_subtitle",
                created_at="2026-04-19T10:00:00",
            )
        ],
    )


def test_lookup_transcript_supports_keyword_filter() -> None:
    result = json.loads(execute_tool(_build_record(), "lookup_transcript", {"keyword": "工具调用"}))
    assert result["returned"] == 1
    assert "工具调用" in result["segments"][0]["text"]


def test_get_video_info_uses_note_record_metadata() -> None:
    result = json.loads(execute_tool(_build_record(), "get_video_info", {}))
    assert result["title"] == "测试视频"
    assert result["url"] == "https://www.bilibili.com/video/BV1xx411c7mD?p=2"
    assert result["video_id"] == "BV1xx411c7mD"


def test_get_note_content_returns_latest_markdown() -> None:
    result = json.loads(execute_tool(_build_record(), "get_note_content", {}))
    assert "完整笔记内容" in result["markdown"]
