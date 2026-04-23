from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class CollectedInput:
    source_type: str
    source_name: str
    collected_at: datetime
    path: Path


@dataclass(slots=True)
class ManualIngestRequest:
    text: str
    source_name: str = "manual"

