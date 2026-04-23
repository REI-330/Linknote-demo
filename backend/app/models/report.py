from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DailyReportItem:
    item_id: str
    dedupe_key: str
    source_url: str
    source_title: str
    source_context: str
    source_origins: list[str]
    collected_at: str
    status: str
    has_note: bool
    failure_code: str = ""
    failure_title: str = ""
    failure_hint: str = ""
    versions: int = 0
    detail_path: str = ""


@dataclass(slots=True)
class DailyReportSummary:
    report_date: str
    total_items: int
    pending_items: int
    completed_items: int
    failed_items: int
    items: list[DailyReportItem] = field(default_factory=list)
