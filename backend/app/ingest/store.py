from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from ..config.settings import AppConfig, ensure_runtime_dirs
from ..models.ingest import CollectedInput


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    return cleaned or "input"


def inbox_date_dir(config: AppConfig, report_date: date) -> Path:
    return config.paths.inbox_dir / report_date.isoformat()


def store_text_input(config: AppConfig, text: str, source_name: str, source_type: str, report_date: date) -> CollectedInput:
    ensure_runtime_dirs(config)
    target_dir = inbox_date_dir(config, report_date)
    target_dir.mkdir(parents=True, exist_ok=True)
    collected_at = datetime.now()
    file_name = f"{collected_at.strftime('%H%M%S')}-{_slugify(source_name)}.txt"
    path = target_dir / file_name
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return CollectedInput(
        source_type=source_type,
        source_name=source_name,
        collected_at=collected_at,
        path=path,
    )

