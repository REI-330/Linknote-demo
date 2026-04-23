from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from ..models.note import NoteRecord, NoteVersion, TranscriptSegment


def build_note_chat_context(
    record: NoteRecord,
    question: str,
    chunks: list[dict[str, object]] | None = None,
) -> tuple[str, list[dict[str, object]]]:
    latest_version = record.versions[-1] if record.versions else None
    retrieved_chunks = chunks if chunks is not None else _retrieve_chunks(record, latest_version, question)
    normalized_chunks = _normalize_chunks(record, retrieved_chunks)
    context = (
        _build_context(normalized_chunks)
        if normalized_chunks
        else "（未检索到足够相关的内容，请基于现有信息谨慎回答）"
    )
    return context, _build_sources(normalized_chunks)


def _retrieve_chunks(record: NoteRecord, version: NoteVersion | None, question: str) -> list[dict[str, object]]:
    source_url = _resolve_source_url(record)
    quotas = {"meta": 1, "markdown": 2, "transcript": 3}
    candidates = {
        "meta": _build_meta_chunk(record, source_url),
        "markdown": _chunk_markdown(version.markdown if version else "", source_url),
        "transcript": _chunk_transcript(record.transcript_segments, source_url),
    }
    results: list[dict[str, object]] = []
    for source_type, limit in quotas.items():
        scored = [
            {**item, "score": _score_text(question, item["text"])}
            for item in candidates[source_type]
        ]
        ranked = sorted(scored, key=lambda item: int(item["score"]), reverse=True)
        results.extend(
            {
                "text": item["text"],
                "metadata": item["metadata"],
            }
            for item in ranked[:limit]
            if int(item["score"]) > 0
        )
    return results


def _chunk_markdown(markdown: str, source_url: str) -> list[dict[str, object]]:
    sections = re.split(r"(?=^#{2,3}\s)", markdown, flags=re.MULTILINE)
    chunks: list[dict[str, object]] = []
    for section in sections:
        text = section.strip()
        if len(text) < 30:
            continue
        heading_match = re.match(r"^(#{2,3})\s+(.+)", text)
        title = heading_match.group(2).strip() if heading_match else "intro"
        chunks.append(
            {
                "text": text,
                "metadata": {
                    "source_type": "markdown",
                    "section_title": title,
                    "title": f"笔记 / {title}",
                    "jump_url": _extract_first_jump_url(text) or source_url,
                },
            }
        )
    return chunks


def _chunk_transcript(
    segments: list[TranscriptSegment],
    source_url: str,
    window_size: int = 15,
    overlap: int = 3,
) -> list[dict[str, object]]:
    if not segments:
        return []
    chunks: list[dict[str, object]] = []
    step = max(window_size - overlap, 1)
    for index in range(0, len(segments), step):
        window = segments[index : index + window_size]
        if not window:
            break
        text = "\n".join(f"[{segment.start:.0f}s] {segment.text}" for segment in window if segment.text.strip())
        if not text.strip():
            continue
        chunks.append(
            {
                "text": text,
                "metadata": {
                    "source_type": "transcript",
                    "start_time": window[0].start,
                    "end_time": window[-1].end,
                    "title": f"转录 / {_format_time(window[0].start)} - {_format_time(window[-1].end)}",
                    "jump_url": _build_jump_url(source_url, window[0].start),
                },
            }
        )
    return chunks


def _build_meta_chunk(record: NoteRecord, source_url: str) -> list[dict[str, object]]:
    parts: list[str] = []
    if record.source_title.strip():
        parts.append(f"视频标题：{record.source_title}")
    if record.metadata.get("uploader"):
        parts.append(f"作者：{record.metadata['uploader']}")
    if record.metadata.get("description"):
        parts.append(f"简介：{str(record.metadata['description'])[:500]}")
    tags = record.metadata.get("tags")
    if isinstance(tags, list) and tags:
        parts.append(f"标签：{', '.join(str(item) for item in tags[:20])}")
    if record.metadata.get("duration"):
        parts.append(f"时长：{int(float(record.metadata['duration']))} 秒")
    if record.source_url.strip():
        parts.append(f"链接：{record.source_url}")
    if not parts:
        return []
    return [
        {
            "text": "\n".join(parts),
            "metadata": {
                "source_type": "meta",
                "title": "视频信息",
                "jump_url": source_url,
            },
        }
    ]


def _build_context(chunks: list[dict[str, object]]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        source_type = meta.get("source_type", "unknown")
        if source_type == "meta":
            label = "[视频信息]"
        elif source_type == "markdown":
            label = f"[笔记 - {meta.get('section_title', '')}]"
        else:
            label = f"[转录 - {meta.get('start_time', 0):.0f}s~{meta.get('end_time', 0):.0f}s]"
        parts.append(f"{label}\n{chunk['text']}")
    return "\n\n".join(parts)


def _build_sources(chunks: list[dict[str, object]]) -> list[dict[str, object]]:
    sources: list[dict[str, object]] = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        item = {
            "text": chunk["text"],
            "source_type": meta.get("source_type", "unknown"),
            "title": meta.get("title") or _fallback_source_title(meta),
        }
        if meta.get("section_title"):
            item["section_title"] = meta["section_title"]
        if meta.get("start_time") is not None:
            item["start_time"] = meta["start_time"]
        if meta.get("end_time") is not None:
            item["end_time"] = meta["end_time"]
        if meta.get("jump_url"):
            item["jump_url"] = meta["jump_url"]
        sources.append(item)
    return sources


def _normalize_chunks(record: NoteRecord, chunks: list[dict[str, object]]) -> list[dict[str, object]]:
    source_url = _resolve_source_url(record)
    normalized: list[dict[str, object]] = []
    for chunk in chunks:
        text = str(chunk.get("text", "") or "").strip()
        if not text:
            continue
        metadata = dict(chunk.get("metadata", {}) or {})
        source_type = str(metadata.get("source_type") or "unknown")
        if source_type == "markdown":
            section_title = str(metadata.get("section_title") or _infer_section_title(text) or "片段")
            metadata["section_title"] = section_title
            metadata.setdefault("title", f"笔记 / {section_title}")
            metadata.setdefault("jump_url", _extract_first_jump_url(text) or source_url)
        elif source_type == "transcript":
            start_time = float(metadata.get("start_time") or 0)
            end_time = float(metadata.get("end_time") or start_time)
            metadata["start_time"] = start_time
            metadata["end_time"] = end_time
            metadata.setdefault("title", f"转录 / {_format_time(start_time)} - {_format_time(end_time)}")
            metadata.setdefault("jump_url", _build_jump_url(source_url, start_time))
        elif source_type == "meta":
            metadata.setdefault("title", "视频信息")
            metadata.setdefault("jump_url", source_url)
        normalized.append({"text": text, "metadata": metadata})
    return normalized


def _score_text(query: str, text: str) -> int:
    normalized_query = query.lower().strip()
    normalized_text = text.lower()
    if not normalized_query or not normalized_text:
        return 0

    score = 0
    if normalized_query in normalized_text:
        score += 20

    for token in _query_tokens(normalized_query):
        if token in normalized_text:
            score += max(1, min(8, len(token)))
    return score


def _query_tokens(query: str) -> list[str]:
    raw_tokens = re.findall(r"[a-z0-9_+-]+|[\u4e00-\u9fff]+", query)
    tokens: list[str] = []
    for token in raw_tokens:
        clean = token.strip()
        if len(clean) < 2:
            continue
        tokens.append(clean)
        if re.fullmatch(r"[\u4e00-\u9fff]+", clean) and len(clean) > 4:
            tokens.extend(clean[index : index + 2] for index in range(len(clean) - 1))
    seen: set[str] = set()
    unique_tokens: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            unique_tokens.append(token)
    return unique_tokens


def _resolve_source_url(record: NoteRecord) -> str:
    canonical_url = str(record.metadata.get("canonical_url") or "").strip()
    if canonical_url:
        return canonical_url
    return record.source_url.strip()


def _build_jump_url(source_url: str, seconds: float) -> str:
    base_url = source_url.strip()
    if not base_url:
        return ""
    parsed = urlparse(base_url)
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key != "t"]
    query.append(("t", str(max(0, int(seconds)))))
    return urlunparse(parsed._replace(query=urlencode(query)))


def _extract_first_jump_url(markdown: str) -> str:
    markdown_link = re.search(r"\((https?://[^)\s]+)\)", markdown)
    if markdown_link:
        return markdown_link.group(1)
    raw_link = re.search(r"https?://\S+", markdown)
    if raw_link:
        return raw_link.group(0).rstrip(").,]")
    return ""


def _infer_section_title(markdown: str) -> str:
    heading_match = re.match(r"^(#{2,3})\s+(.+)", markdown.strip())
    if not heading_match:
        return ""
    return heading_match.group(2).strip()


def _format_time(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    minutes = total_seconds // 60
    remain_seconds = total_seconds % 60
    hours = minutes // 60
    remain_minutes = minutes % 60
    if hours > 0:
        return f"{hours}:{remain_minutes:02}:{remain_seconds:02}"
    return f"{remain_minutes:02}:{remain_seconds:02}"


def _fallback_source_title(metadata: dict[str, object]) -> str:
    source_type = str(metadata.get("source_type") or "unknown")
    if source_type == "markdown":
        return f"笔记 / {metadata.get('section_title') or '片段'}"
    if source_type == "transcript":
        return f"转录 / {_format_time(float(metadata.get('start_time') or 0))}"
    return "视频信息"
