from __future__ import annotations

import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

from ..config.settings import AppConfig
from .note_records import load_note_record


def apply_retention_policy(config: AppConfig, *, today: date | None = None) -> None:
    current_day = today or date.today()
    keep_from = current_day - timedelta(days=max(config.retention.days, 1) - 1)
    _prune_dated_directories(config.paths.inbox_dir, keep_from)
    _prune_dated_directories(config.paths.reports_dir, keep_from)
    _prune_note_directories(config, keep_from)


def _prune_dated_directories(root: Path, keep_from: date) -> None:
    if not root.exists():
        return
    for path in root.iterdir():
        if not path.is_dir():
            continue
        folder_day = _parse_folder_date(path.name)
        if folder_day is None or folder_day >= keep_from:
            continue
        shutil.rmtree(path, ignore_errors=True)


def _prune_note_directories(config: AppConfig, keep_from: date) -> None:
    notes_root = config.paths.workspace_dir / "notes"
    if not notes_root.exists():
        return
    for path in notes_root.iterdir():
        if not path.is_dir():
            continue
        record = load_note_record(config, path.name)
        if record is not None:
            try:
                report_day = datetime.strptime(record.report_date, "%Y-%m-%d").date()
            except ValueError:
                report_day = date.fromtimestamp(path.stat().st_mtime)
        else:
            report_day = date.fromtimestamp(path.stat().st_mtime)
        if report_day < keep_from:
            shutil.rmtree(path, ignore_errors=True)


def _parse_folder_date(name: str) -> date | None:
    try:
        return datetime.strptime(name, "%Y-%m-%d").date()
    except ValueError:
        return None
