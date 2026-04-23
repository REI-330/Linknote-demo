from __future__ import annotations

from collections.abc import Callable

from ..analysis import OpenAICompatibleAnalyzer
from ..config.settings import AppConfig
from ..models.media import TranscriptResult
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
    if analyzer is None:
        raise RuntimeError("OpenAI-compatible transcription requires an analyzer instance.")
    return analyzer.transcribe(audio_path, config.transcriber)
