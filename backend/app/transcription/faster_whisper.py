from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..config.settings import TranscriberConfig
from ..models.media import TranscriptResult, TranscriptSegmentResult

try:
    from faster_whisper import WhisperModel
except ModuleNotFoundError:  # pragma: no cover - runtime dependency gate
    WhisperModel = None


_MODEL_CACHE: dict[tuple[str, str, str], Any] = {}


def transcribe_with_faster_whisper(
    audio_path: str,
    transcriber_config: TranscriberConfig,
    *,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
) -> TranscriptResult:
    if WhisperModel is None:
        raise RuntimeError("faster-whisper is not installed. Run `python -m pip install faster-whisper` in the backend environment.")

    model_name = _resolved_model_name(transcriber_config)
    device = os.getenv("LINKNOTE_WHISPER_DEVICE", "cpu").strip() or "cpu"
    compute_type = os.getenv("LINKNOTE_WHISPER_COMPUTE_TYPE", "int8").strip() or "int8"
    model = _load_model(model_name, device, compute_type)
    segments_iter, info = model.transcribe(
        audio_path,
        language=(transcriber_config.language or "").strip() or None,
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=False,
    )

    segments: list[TranscriptSegmentResult] = []
    for segment in segments_iter:
        text = str(getattr(segment, "text", "")).strip()
        if not text:
            continue
        current = TranscriptSegmentResult(
            start=float(getattr(segment, "start", 0)),
            end=float(getattr(segment, "end", 0)),
            text=text,
        )
        segments.append(current)
        if progress_callback is not None and len(segments) % 20 == 0:
            progress_callback(
                {
                    "segment_count": len(segments),
                    "transcribed_seconds": current.end,
                }
            )

    if progress_callback is not None and segments:
        progress_callback(
            {
                "segment_count": len(segments),
                "transcribed_seconds": segments[-1].end,
            }
        )

    full_text = " ".join(segment.text for segment in segments).strip()
    if not full_text:
        raise RuntimeError("Local transcription returned empty text.")

    return TranscriptResult(
        language=str(getattr(info, "language", "") or transcriber_config.language or "").strip() or None,
        full_text=full_text,
        segments=segments,
        raw={
            "source": "faster_whisper",
            "model_name": model_name,
            "device": device,
            "compute_type": compute_type,
        },
    )


def _resolved_model_name(transcriber_config: TranscriberConfig) -> str:
    candidate = (transcriber_config.model_name or "").strip()
    if candidate and candidate.lower() != "whisper-1":
        return candidate
    return os.getenv("LINKNOTE_LOCAL_WHISPER_MODEL", "small").strip() or "small"


def _load_model(model_name: str, device: str, compute_type: str) -> Any:
    key = (model_name, device, compute_type)
    cached = _MODEL_CACHE.get(key)
    if cached is not None:
        return cached
    download_root = Path(
        os.getenv(
            "LINKNOTE_WHISPER_CACHE_DIR",
            str(Path.home() / "linknote-whisper-cache"),
        )
    ).expanduser()
    download_root.mkdir(parents=True, exist_ok=True)
    model = WhisperModel(model_name, device=device, compute_type=compute_type, download_root=str(download_root))
    _MODEL_CACHE[key] = model
    return model
