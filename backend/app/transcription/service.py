from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ..analysis import OpenAICompatibleAnalyzer
from ..config.settings import AppConfig, resolve_provider_api_key
from ..models.media import TranscriptResult
from ..services.provider_catalog import resolve_transcriber_provider
from .faster_whisper import transcribe_with_faster_whisper


def transcribe_audio(
    config: AppConfig,
    audio_path: str,
    *,
    analyzer: OpenAICompatibleAnalyzer | None = None,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
) -> TranscriptResult:
    transcriber_type = (config.transcriber.type or "").strip().lower()
    if transcriber_type == "faster_whisper":
        return transcribe_with_faster_whisper(audio_path, config.transcriber, progress_callback=progress_callback)
    transcriber_provider = resolve_transcriber_provider(config)
    transcriber_api_key = resolve_provider_api_key(transcriber_provider)
    if not transcriber_api_key:
        raise RuntimeError("Transcription provider API key is not configured.")

    transcription_analyzer = analyzer
    if transcription_analyzer is None or transcription_analyzer.provider.provider_id != transcriber_provider.provider_id:
        transcription_analyzer = OpenAICompatibleAnalyzer(
            transcriber_provider,
            transcriber_api_key,
            Path(audio_path).resolve().parent / "checkpoints",
        )
    return transcription_analyzer.transcribe(audio_path, config.transcriber)
