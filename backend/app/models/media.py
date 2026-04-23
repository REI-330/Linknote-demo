from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TranscriptSegmentResult:
    start: float
    end: float
    text: str
    speaker: str = ""


@dataclass(slots=True)
class TranscriptResult:
    language: str | None
    full_text: str
    segments: list[TranscriptSegmentResult]
    raw: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class MediaDownloadResult:
    source_url: str
    canonical_url: str
    platform: str
    video_id: str
    title: str
    duration: float
    cover_url: str
    description: str
    uploader: str
    tags: list[str] = field(default_factory=list)
    audio_path: str = ""
    video_path: str = ""
    raw_info: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class AnalysisRunResult:
    markdown: str
    source_basis: str
    transcript: TranscriptResult
    media: MediaDownloadResult
    model_name: str
    provider_id: str
