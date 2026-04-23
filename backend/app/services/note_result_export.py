from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from ..config.settings import AppConfig
from ..models.media import MediaDownloadResult, TranscriptResult, TranscriptSegmentResult
from ..models.note import NoteRecord
from .file_io import safe_write_json
from .note_records import note_root


def note_result_path(config: AppConfig, item_id: str) -> Path:
    return note_root(config, item_id) / "artifacts" / f"{item_id}.json"


def write_bilinote_note_result(
    config: AppConfig,
    record: NoteRecord,
    *,
    media: MediaDownloadResult,
    transcript: TranscriptResult,
    markdown: str,
) -> Path:
    path = note_result_path(config, record.item_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": record.item_id,
        "markdown": markdown,
        "transcript": {
            "language": transcript.language,
            "full_text": transcript.full_text,
            "segments": [asdict(segment) for segment in transcript.segments],
            "raw": transcript.raw,
        },
        "audio_meta": _audio_meta_payload(media),
    }
    safe_write_json(path, payload)
    return path


def ensure_note_result_snapshot(config: AppConfig, record: NoteRecord) -> Path | None:
    latest_version = record.versions[-1] if record.versions else None
    if latest_version is None:
        return None

    transcript = TranscriptResult(
        language=str(record.metadata.get("language") or "zh"),
        full_text="\n".join(segment.text for segment in record.transcript_segments if segment.text.strip()),
        segments=[
            TranscriptSegmentResult(
                start=segment.start,
                end=segment.end,
                text=segment.text,
                speaker=segment.speaker,
            )
            for segment in record.transcript_segments
        ],
        raw={},
    )
    media = MediaDownloadResult(
        source_url=record.source_url,
        canonical_url=str(record.metadata.get("canonical_url") or record.source_url),
        platform=str(record.metadata.get("platform") or "bilibili"),
        video_id=str(record.metadata.get("video_id") or ""),
        title=record.source_title,
        duration=float(record.metadata.get("duration") or 0),
        cover_url=str(record.metadata.get("cover_url") or ""),
        description=str(record.metadata.get("description") or ""),
        uploader=str(record.metadata.get("uploader") or ""),
        tags=[str(item) for item in record.metadata.get("tags", [])] if isinstance(record.metadata.get("tags"), list) else [],
        audio_path="",
        video_path="",
        raw_info=dict(record.metadata.get("raw_info") or {}),
    )
    return write_bilinote_note_result(
        config,
        record,
        media=media,
        transcript=transcript,
        markdown=latest_version.markdown,
    )


def _audio_meta_payload(media: MediaDownloadResult) -> dict[str, object]:
    raw_info = dict(media.raw_info)
    if media.title and not raw_info.get("title"):
        raw_info["title"] = media.title
    if media.uploader and not raw_info.get("uploader"):
        raw_info["uploader"] = media.uploader
    if media.description and not raw_info.get("description"):
        raw_info["description"] = media.description
    if media.tags and not raw_info.get("tags"):
        raw_info["tags"] = media.tags
    if media.canonical_url and not raw_info.get("webpage_url"):
        raw_info["webpage_url"] = media.canonical_url

    return {
        "source_url": media.source_url,
        "canonical_url": media.canonical_url,
        "platform": media.platform,
        "video_id": media.video_id,
        "title": media.title,
        "duration": media.duration,
        "cover_url": media.cover_url,
        "description": media.description,
        "uploader": media.uploader,
        "tags": media.tags,
        "audio_path": media.audio_path,
        "video_path": media.video_path,
        "raw_info": raw_info,
    }
