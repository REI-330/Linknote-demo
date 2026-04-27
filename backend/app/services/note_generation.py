from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import os
from pathlib import Path

from ..analysis import GPTSource, OpenAICompatibleAnalyzer, UniversalGPT
from ..config.settings import AppConfig, resolve_provider_api_key
from ..downloaders import BilibiliDownloader
from ..models.media import AnalysisRunResult, MediaDownloadResult, TranscriptResult
from ..models.note import NoteRecord, TranscriptSegment
from ..transcription import transcribe_audio
from .file_io import safe_write_json, safe_write_text
from .ffmpeg import resolve_ffmpeg_command
from .note_markdown import (
    SCREENSHOT_BASE_URL,
    insert_screenshots,
    prepend_source_link,
    replace_content_markers,
    screenshot_output_dir,
)
from .note_records import append_note_version, mark_note_failed, save_note_record
from .note_result_export import write_bilinote_note_result
from .provider_catalog import resolve_analysis_target
from .vector_store import VectorStoreManager


def _timestamp_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _format_duration(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _running_progress(
    *,
    stage: str,
    detail: str,
    step: str,
    started_at: str,
) -> dict[str, object]:
    return {
        "stage": stage,
        "step": step,
        "detail": detail,
        "started_at": started_at,
        "updated_at": _timestamp_now(),
    }


def _set_running_progress(
    config: AppConfig,
    record: NoteRecord,
    *,
    stage: str,
    detail: str,
    step: str,
    save: bool = True,
) -> None:
    started_at = str(record.analysis_progress.get("started_at", "")).strip() or _timestamp_now()
    record.analysis_progress = _running_progress(
        stage=stage,
        detail=detail,
        step=step,
        started_at=started_at,
    )
    if save:
        save_note_record(config, record)


def _populate_media_metadata(record: NoteRecord, media: MediaDownloadResult) -> None:
    record.metadata.update(
        {
            "platform": media.platform,
            "video_id": media.video_id,
            "canonical_url": media.canonical_url,
            "cover_url": media.cover_url,
            "duration": media.duration,
            "uploader": media.uploader,
            "description": media.description,
            "tags": media.tags,
            "raw_info": media.raw_info,
        }
    )


def _set_transcript_segments(record: NoteRecord, transcript: TranscriptResult) -> None:
    record.transcript_segments = [
        TranscriptSegment(
            start=segment.start,
            end=segment.end,
            text=segment.text,
            speaker=segment.speaker,
        )
        for segment in transcript.segments
    ]


def _classify_analysis_error(message: str) -> dict[str, object]:
    normalized = message.strip()
    lower = normalized.lower()

    if ("api key is not configured" in lower) or ("environment variable `" in lower and "api" in lower and "not set" in lower):
        return {
            "code": "config_missing_api_key",
            "title": "Model API Key not configured",
            "hint": "Check the selected analysis provider in Settings and configure its API key before retrying.",
            "actions": ["settings"],
        }
    if "incorrect api key provided" in lower or "invalid_api_key" in lower or "invalid api key" in lower:
        return {
            "code": "config_invalid_api_key",
            "title": "Model API Key is invalid",
            "hint": "The current provider rejected the configured API key. Update it in Settings and retry.",
            "actions": ["settings", "retry"],
        }
    if "no analysis provider is configured" in lower or "no enabled model provider" in lower:
        return {
            "code": "config_missing_provider",
            "title": "No analysis provider selected",
            "hint": "Choose an enabled provider in Settings and save before running analysis again.",
            "actions": ["settings"],
        }
    if "requested model provider is not enabled" in lower:
        return {
            "code": "config_missing_provider",
            "title": "Selected analysis provider is unavailable",
            "hint": "The selected provider is disabled or missing. Pick another provider in Settings and save.",
            "actions": ["settings"],
        }
    if "no analysis model is configured" in lower or "no configured model is available" in lower or "requested model is not enabled" in lower:
        return {
            "code": "config_missing_model",
            "title": "No analysis model selected",
            "hint": "Pick an enabled analysis model in Settings. The system no longer auto-falls back to the first model in the list.",
            "actions": ["settings"],
        }
    if "transcription provider api key is not configured" in lower:
        return {
            "code": "config_missing_transcriber_api_key",
            "title": "Transcription provider API key is missing",
            "hint": "The current transcription provider has no API key configured. Update the transcriber settings or switch to faster-whisper.",
            "actions": ["settings", "retry"],
        }
    if "no transcription provider is configured" in lower or "requested transcription provider is not enabled" in lower:
        return {
            "code": "config_missing_transcriber_provider",
            "title": "No transcription provider is available",
            "hint": "Choose an available transcription provider in Settings, or switch the transcriber to faster-whisper.",
            "actions": ["settings", "retry"],
        }
    if "no access to model whisper-1" in lower or ("whisper-1" in lower and "403" in lower):
        return {
            "code": "transcriber_model_access_denied",
            "title": "The current transcription model is unavailable",
            "hint": "The selected transcription provider does not have access to whisper-1. Switch the transcriber provider or use faster-whisper.",
            "actions": ["settings", "retry"],
        }
    if "unable to extract bv id" in lower:
        return {
            "code": "invalid_bilibili_url",
            "title": "This is not a recognizable Bilibili video URL",
            "hint": "Use a standard video page URL with a BV id and retry.",
            "actions": ["source"],
        }
    if "yt-dlp is not installed" in lower:
        return {
            "code": "dependency_missing_ytdlp",
            "title": "yt-dlp is missing",
            "hint": "Install yt-dlp in the backend environment before retrying analysis.",
            "actions": ["settings"],
        }
    if "faster-whisper is not installed" in lower:
        return {
            "code": "dependency_missing_faster_whisper",
            "title": "faster-whisper is missing",
            "hint": "The current transcriber is set to faster-whisper, but the package is not installed in the backend environment.",
            "actions": ["settings", "retry"],
        }
    if "no usable bilibili cookie source was available" in lower:
        return {
            "code": "bilibili_cookies_required",
            "title": "This Bilibili video requires cookies",
            "hint": "Configure cookies.txt or enable browser cookies fallback in Settings, then retry.",
            "actions": ["settings", "retry", "source"],
        }
    if "ffmpeg" in lower or "ffprobe" in lower:
        return {
            "code": "dependency_missing_ffmpeg",
            "title": "Audio processing dependency is unavailable",
            "hint": "The current environment is missing ffmpeg or ffprobe. Fix that dependency and retry.",
            "actions": ["settings", "retry"],
        }
    if "http error 412" in lower or "precondition failed" in lower:
        return {
            "code": "bilibili_request_blocked",
            "title": "Bilibili request was blocked",
            "hint": "Try a standard BV video URL first. If it still fails, configure cookies.txt or enable browser cookies fallback and retry.",
            "actions": ["settings", "retry", "source"],
        }
    if "subtitle fetch failed" in lower or "no subtitle was found and audio download did not produce a file" in lower:
        return {
            "code": "transcript_unavailable",
            "title": "No subtitle or transcribable audio was available",
            "hint": "The video may be restricted, audio download may have failed, or the source itself may not be transcribable.",
            "actions": ["settings", "retry", "source"],
        }
    return {
        "code": "analysis_failed",
        "title": "Analysis failed",
        "hint": "Check the analysis model settings and cookies configuration, then retry.",
        "actions": ["settings", "retry"],
    }


def run_note_analysis(
    config: AppConfig,
    record: NoteRecord,
    *,
    provider_id: str | None = None,
    model_name: str | None = None,
) -> NoteRecord:
    record.status = "running"
    record.last_error = ""
    record.last_error_code = ""
    record.last_error_title = ""
    record.last_error_hint = ""
    record.analysis_progress = _running_progress(
        stage="starting",
        detail="Preparing downloader, model provider, and workspace.",
        step="preparing",
        started_at=_timestamp_now(),
    )
    save_note_record(config, record)
    try:
        result = _analyze_bilibili_note(config, record, provider_id=provider_id, model_name=model_name)
    except Exception as exc:
        failure = _classify_analysis_error(str(exc))
        return mark_note_failed(
            config,
            record,
            str(exc),
            code=str(failure["code"]),
            title=str(failure["title"]),
            hint=str(failure["hint"]),
        )

    _set_transcript_segments(record, result.transcript)
    _populate_media_metadata(record, result.media)
    record.metadata["transcript_source"] = result.source_basis
    record.analysis_progress = {
        "stage": "saving",
        "step": "success",
        "detail": "Saving generated note and search index.",
        "started_at": str(record.analysis_progress.get("started_at", "")),
        "updated_at": _timestamp_now(),
    }
    save_note_record(config, record)
    updated = append_note_version(
        config,
        record,
        label=f"分析版本 {len(record.versions) + 1}",
        markdown=result.markdown,
        source_basis=result.source_basis,
        model_name=result.model_name,
        provider_id=result.provider_id,
    )
    _index_note_vector_store(config, updated.item_id)
    _cleanup_intermediate_files(config, updated)
    return updated


def _analyze_bilibili_note(
    config: AppConfig,
    record: NoteRecord,
    *,
    provider_id: str | None = None,
    model_name: str | None = None,
) -> AnalysisRunResult:
    _set_running_progress(
        config,
        record,
        stage="selecting_model",
        detail="Resolving the configured analysis provider and model.",
        step="preparing",
    )
    provider, selected_model = resolve_analysis_target(config, provider_id=provider_id, model_name=model_name)
    api_key = resolve_provider_api_key(provider)
    if not api_key:
        raise RuntimeError("API key is not configured.")

    note_dir = config.paths.workspace_dir / "notes" / record.item_id
    artifact_dir = note_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    analyzer = OpenAICompatibleAnalyzer(provider, api_key, note_dir / "checkpoints")
    downloader = BilibiliDownloader(
        artifact_dir,
        project_root=config.project_root,
        ffmpeg_location=resolve_ffmpeg_command(config.project_root),
        cookies_file=config.bilibili.cookies_file,
        use_browser_cookies=config.bilibili.use_browser_cookies,
    )

    _set_running_progress(
        config,
        record,
        stage="fetching_subtitles",
        detail="Checking whether the Bilibili video has platform subtitles.",
        step="preparing",
    )
    transcript = downloader.fetch_subtitles(record.source_url)
    source_basis = "platform_subtitle"
    _set_running_progress(
        config,
        record,
        stage="downloading_media",
        detail="Downloading media artifacts required by the analysis pipeline.",
        step="preparing",
    )
    media = downloader.fetch_media(
        record.source_url,
        download_audio=transcript is None,
        download_video=config.analysis.enable_screenshots,
    )
    _populate_media_metadata(record, media)
    save_note_record(config, record)
    if transcript is None:
        if not media.audio_path:
            raise RuntimeError("No subtitle was found and audio download did not produce a file.")
        duration_text = _format_duration(media.duration)
        transcriber_name = (config.transcriber.model_name or config.transcriber.type or "transcriber").strip()
        _set_running_progress(
            config,
            record,
            stage="transcribing_audio",
            detail=f"No platform subtitle was available. Local transcription is processing {duration_text} of audio with {transcriber_name}.",
            step="running",
        )

        def on_transcription_progress(update: dict[str, object]) -> None:
            transcribed_seconds = float(update.get("transcribed_seconds", 0) or 0)
            segment_count = int(update.get("segment_count", 0) or 0)
            detail = f"Local transcription is processing {duration_text} of audio."
            if transcribed_seconds > 0:
                detail = (
                    f"Local transcription reached about {_format_duration(transcribed_seconds)} "
                    f"of {duration_text} across {segment_count} segments."
                )
            _set_running_progress(
                config,
                record,
                stage="transcribing_audio",
                detail=detail,
                step="running",
            )

        transcript = transcribe_audio(config, media.audio_path, analyzer=analyzer, progress_callback=on_transcription_progress)
        source_basis = "audio_transcription"
    _set_transcript_segments(record, transcript)
    record.metadata["transcript_source"] = source_basis
    _set_running_progress(
        config,
        record,
        stage="summarizing",
        detail=f"Transcript is ready with {len(transcript.segments)} segments. Generating the note with {selected_model}.",
        step="running",
    )

    summarizer = UniversalGPT(
        analyzer.client,
        selected_model,
        checkpoint_dir=note_dir / "checkpoints",
    )
    markdown = summarizer.summarize(
        GPTSource(
            title=media.title,
            segment=transcript.segments,
            tags=media.tags,
            screenshot=config.analysis.enable_screenshots,
            link=config.analysis.enable_source_links,
            style=config.analysis.note_style,
            extras="",
            _format=_analysis_formats(config),
            video_img_urls=[],
            checkpoint_key=record.item_id,
        )
    ).strip()
    markdown = _post_process_markdown(config, markdown, media, record.source_url)

    _write_json(artifact_dir / "media.json", asdict(media))
    _write_json(artifact_dir / "transcript.json", _transcript_payload(transcript))
    safe_write_text(artifact_dir / "analysis.md", markdown)
    write_bilinote_note_result(
        config,
        record,
        media=media,
        transcript=transcript,
        markdown=markdown,
    )

    return AnalysisRunResult(
        markdown=markdown,
        source_basis=source_basis,
        transcript=transcript,
        media=media,
        model_name=selected_model,
        provider_id=provider.provider_id,
    )


def _analysis_formats(config: AppConfig) -> list[str]:
    formats = [config.analysis.note_format] if config.analysis.note_format else []
    if config.analysis.enable_source_links and "link" not in formats:
        formats.append("link")
    if config.analysis.enable_screenshots and "screenshot" not in formats:
        formats.append("screenshot")
    return formats


def _write_json(path: Path, payload: dict[str, object]) -> None:
    safe_write_json(path, payload)


def _transcript_payload(transcript: TranscriptResult) -> dict[str, object]:
    return {
        "language": transcript.language,
        "full_text": transcript.full_text,
        "segments": [asdict(segment) for segment in transcript.segments],
        "raw": transcript.raw,
    }


def _post_process_markdown(
    config: AppConfig,
    markdown: str,
    media: MediaDownloadResult,
    fallback_source_url: str,
) -> str:
    processed = markdown
    source_url = media.canonical_url or fallback_source_url

    if config.analysis.enable_screenshots:
        if not media.video_path:
            raise RuntimeError("Screenshot insertion requires a downloaded video file.")
        processed = insert_screenshots(
            processed,
            video_path=media.video_path,
            output_dir=screenshot_output_dir(config.project_root),
            base_url=SCREENSHOT_BASE_URL,
        )

    if config.analysis.enable_source_links:
        processed = replace_content_markers(processed, source_url)

    return prepend_source_link(processed, source_url)


def _cleanup_intermediate_files(config: AppConfig, record: NoteRecord) -> None:
    if not config.retention.cleanup_intermediate:
        return
    artifact_dir = config.paths.workspace_dir / "notes" / record.item_id / "artifacts"
    if not artifact_dir.exists():
        return
    for pattern in ("*.mp3", "*.m4a", "*.mp4", "*.webm", "*.srt", "*.json3", "*.vtt", "*.part"):
        for path in artifact_dir.glob(pattern):
            path.unlink(missing_ok=True)


def _index_note_vector_store(config: AppConfig, item_id: str) -> None:
    try:
        store = VectorStoreManager(config)
        if not store.is_available:
            return
        store.index_task(item_id)
    except Exception:
        return
