from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: str = ""


@dataclass(slots=True)
class NoteVersion:
    version_id: str
    label: str
    markdown: str
    source_basis: str
    created_at: str
    model_name: str = ""
    provider_id: str = ""


@dataclass(slots=True)
class NoteRecord:
    item_id: str
    report_date: str
    status: str
    source_url: str
    source_title: str
    source_context: str
    source_origins: list[str]
    transcript_segments: list[TranscriptSegment] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)
    analysis_progress: dict[str, object] = field(default_factory=dict)
    versions: list[NoteVersion] = field(default_factory=list)
    last_error: str = ""
    last_error_code: str = ""
    last_error_title: str = ""
    last_error_hint: str = ""
