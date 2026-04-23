from __future__ import annotations

from app.models.note import NoteRecord, NoteVersion, TranscriptSegment
from app.services.note_retrieval import build_note_chat_context


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
            TranscriptSegment(start=12, end=20, text="这里提到检索增强和问答来源展开。"),
            TranscriptSegment(start=20, end=28, text="继续解释为什么需要完整暴露引用片段。"),
        ],
        metadata={
            "canonical_url": "https://www.bilibili.com/video/BV1xx411c7mD?p=2",
            "uploader": "tester",
            "description": "一段用于验证问答来源的简介",
            "tags": ["检索增强", "前端交互"],
            "duration": 120,
        },
        versions=[
            NoteVersion(
                version_id="v1",
                label="分析版本 1",
                markdown=(
                    "## 问答来源设计\n"
                    "这一节专门讨论问答来源展开卡片如何展示，"
                    "并且已经保留了 [原片 @ 00:12](https://www.bilibili.com/video/BV1xx411c7mD?p=2&t=12) 链接。"
                ),
                source_basis="platform_subtitle",
                created_at="2026-04-19T10:00:00",
            )
        ],
    )


def test_build_note_chat_context_returns_full_markdown_source_text() -> None:
    _context, sources = build_note_chat_context(_build_record(), "来源设计卡片怎么展示")
    markdown_source = next(source for source in sources if source["source_type"] == "markdown")

    assert "问答来源展开卡片如何展示" in markdown_source["text"]
    assert markdown_source["title"] == "笔记 / 问答来源设计"
    assert markdown_source["jump_url"] == "https://www.bilibili.com/video/BV1xx411c7mD?p=2&t=12"


def test_build_note_chat_context_returns_transcript_jump_url() -> None:
    _context, sources = build_note_chat_context(_build_record(), "为什么需要完整暴露引用片段")
    transcript_source = next(source for source in sources if source["source_type"] == "transcript")

    assert "完整暴露引用片段" in transcript_source["text"]
    assert transcript_source["title"] == "转录 / 00:12 - 00:28"
    assert transcript_source["jump_url"] == "https://www.bilibili.com/video/BV1xx411c7mD?p=2&t=12"


def test_build_note_chat_context_enriches_bilinote_vector_chunks() -> None:
    chunks = [
        {
            "text": "## 问答来源设计\n这里保留了 [原片 @ 00:12](https://www.bilibili.com/video/BV1xx411c7mD?p=2&t=12) 链接。",
            "metadata": {"source_type": "markdown", "section_title": "问答来源设计"},
        },
        {
            "text": "[12s] 这里提到检索增强和问答来源展开。",
            "metadata": {"source_type": "transcript", "start_time": 12, "end_time": 20},
        },
        {
            "text": "视频标题：测试视频\n链接：https://www.bilibili.com/video/BV1xx411c7mD?p=2",
            "metadata": {"source_type": "meta"},
        },
    ]

    _context, sources = build_note_chat_context(_build_record(), "来源设计", chunks)

    markdown_source = next(source for source in sources if source["source_type"] == "markdown")
    transcript_source = next(source for source in sources if source["source_type"] == "transcript")
    meta_source = next(source for source in sources if source["source_type"] == "meta")

    assert markdown_source["title"] == "笔记 / 问答来源设计"
    assert markdown_source["jump_url"] == "https://www.bilibili.com/video/BV1xx411c7mD?p=2&t=12"
    assert transcript_source["title"] == "转录 / 00:12 - 00:20"
    assert transcript_source["jump_url"] == "https://www.bilibili.com/video/BV1xx411c7mD?p=2&t=12"
    assert meta_source["title"] == "视频信息"
    assert meta_source["jump_url"] == "https://www.bilibili.com/video/BV1xx411c7mD?p=2"
