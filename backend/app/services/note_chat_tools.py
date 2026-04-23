from __future__ import annotations

import json

from ..models.note import NoteRecord


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_transcript",
            "description": "查询视频原始转录文本。可按时间范围筛选、按关键词搜索、或获取指定位置的内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "number",
                        "description": "起始时间（秒），例如 0 表示视频开头，60 表示第1分钟",
                    },
                    "end_time": {
                        "type": "number",
                        "description": "结束时间（秒），不传则到末尾",
                    },
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词，返回包含该关键词的转录片段",
                    },
                    "position": {
                        "type": "string",
                        "enum": ["start", "end"],
                        "description": "快捷位置：start=视频开头前30句，end=视频结尾后30句",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_video_info",
            "description": "获取视频的完整元信息，包括标题、作者、简介、标签、时长等。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_note_content",
            "description": "获取 AI 生成的完整笔记内容（Markdown 格式）。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


def execute_tool(record: NoteRecord, tool_name: str, arguments: dict[str, object]) -> str:
    if tool_name == "lookup_transcript":
        return _lookup_transcript(record, arguments)
    if tool_name == "get_video_info":
        return _get_video_info(record)
    if tool_name == "get_note_content":
        return _get_note_content(record)
    return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)


def _lookup_transcript(record: NoteRecord, args: dict[str, object]) -> str:
    segments = record.transcript_segments
    if not segments:
        return json.dumps({"error": "没有转录数据"}, ensure_ascii=False)

    position = str(args.get("position") or "").strip()
    keyword = str(args.get("keyword") or "").strip().lower()
    start_time = _to_float(args.get("start_time"))
    end_time = _to_float(args.get("end_time"))

    if position == "start":
        filtered = segments[:30]
    elif position == "end":
        filtered = segments[-30:]
    else:
        filtered = list(segments)

    if start_time is not None:
        filtered = [segment for segment in filtered if segment.end >= start_time]
    if end_time is not None:
        filtered = [segment for segment in filtered if segment.start <= end_time]
    if keyword:
        filtered = [segment for segment in filtered if keyword in segment.text.lower()]

    truncated = len(filtered) > 50
    filtered = filtered[:50]

    result = {
        "total_segments": len(segments),
        "returned": len(filtered),
        "truncated": truncated,
        "segments": [
            {
                "start": round(segment.start, 1),
                "end": round(segment.end, 1),
                "text": segment.text,
            }
            for segment in filtered
        ],
    }
    return json.dumps(result, ensure_ascii=False)


def _get_video_info(record: NoteRecord) -> str:
    metadata = record.metadata or {}
    raw = metadata.get("raw_info", {}) if isinstance(metadata.get("raw_info"), dict) else {}
    tags = metadata.get("tags")
    info = {
        "title": metadata.get("source_title") or record.source_title,
        "uploader": metadata.get("uploader") or "",
        "description": str(metadata.get("description") or raw.get("description") or "")[:1000],
        "tags": tags[:20] if isinstance(tags, list) else [],
        "duration_seconds": metadata.get("duration") or 0,
        "platform": metadata.get("platform") or "",
        "video_id": metadata.get("video_id") or "",
        "url": metadata.get("canonical_url") or record.source_url,
    }
    info = {key: value for key, value in info.items() if value not in ("", None, [])}
    return json.dumps(info, ensure_ascii=False)


def _get_note_content(record: NoteRecord) -> str:
    latest_version = record.versions[-1] if record.versions else None
    markdown = latest_version.markdown if latest_version else ""
    if len(markdown) > 5000:
        markdown = markdown[:5000] + "\n\n... (内容过长已截断)"
    return json.dumps({"markdown": markdown}, ensure_ascii=False)


def _to_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
