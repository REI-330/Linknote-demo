from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

from ..config.settings import AppConfig
from .file_io import safe_write_json
from .note_records import note_root
from .vector_store import VectorStoreManager


def deleted_items_path(config: AppConfig, report_date: date) -> Path:
    return config.paths.runtime_dir / "deleted-report-items" / f"{report_date.isoformat()}.json"


def load_deleted_item_ids(config: AppConfig, report_date: date) -> set[str]:
    path = deleted_items_path(config, report_date)
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    items = payload.get("item_ids", [])
    if not isinstance(items, list):
        return set()
    return {str(item).strip() for item in items if str(item).strip()}


def save_deleted_item_ids(config: AppConfig, report_date: date, item_ids: set[str]) -> Path:
    path = deleted_items_path(config, report_date)
    safe_write_json(
        path,
        {
            "report_date": report_date.isoformat(),
            "item_ids": sorted(item_ids),
        },
    )
    return path


def delete_failed_report_item(config: AppConfig, item_id: str, report_date: date) -> bool:
    from .report_index import build_daily_report

    report = build_daily_report(config, report_date)
    target = next((item for item in report.items if item.item_id == item_id), None)
    if target is None:
        raise KeyError(item_id)
    if target.status != "failed":
        raise RuntimeError("Only failed report items can be deleted from the card flow.")

    deleted_item_ids = load_deleted_item_ids(config, report_date)
    deleted_item_ids.add(item_id)
    save_deleted_item_ids(config, report_date, deleted_item_ids)
    _remove_note_workspace(config, item_id)
    _remove_vector_index(config, item_id)
    return True


def _remove_note_workspace(config: AppConfig, item_id: str) -> None:
    root = note_root(config, item_id)
    if not root.exists():
        return
    shutil.rmtree(root, ignore_errors=True)


def _remove_vector_index(config: AppConfig, item_id: str) -> None:
    try:
        store = VectorStoreManager(config)
        store.delete_index(item_id)
    except Exception:
        return
