from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

from ..config.settings import AppConfig
from ..ingest.clipboard import collect_clipboard
from ..ingest.wechat import collect_wechat_messages
from ..models.report import DailyReportItem
from .note_generation import run_note_analysis
from .note_records import ensure_note_record
from .notifications import notify_daily_report_ready
from .report_index import build_daily_report
from .retention import apply_retention_policy


@dataclass(slots=True)
class DailyRunResult:
    report_date: str
    collected_sources: list[str]
    analyzed_item_ids: list[str]
    failed_item_ids: list[str]
    total_items: int
    completed_items: int
    failed_items: int
    pending_items: int
    started_at: str
    finished_at: str


_RUN_LOCK = threading.Lock()


def manual_run_daily(config: AppConfig, *, include_wechat: bool = True, include_clipboard: bool | None = None) -> DailyRunResult:
    return _run_daily(config, include_wechat=include_wechat, include_clipboard=include_clipboard, reason="manual")


def scheduled_run_daily(config: AppConfig) -> DailyRunResult:
    return _run_daily(
        config,
        include_wechat=config.schedule.auto_collect_wechat,
        include_clipboard=config.clipboard.include_on_schedule,
        reason="scheduled",
    )


def _run_daily(config: AppConfig, *, include_wechat: bool, include_clipboard: bool | None, reason: str) -> DailyRunResult:
    if not _RUN_LOCK.acquire(blocking=False):
        raise RuntimeError("A daily run is already in progress.")

    started_at = datetime.now()
    collected_sources: list[str] = []
    analyzed_item_ids: list[str] = []
    failed_item_ids: list[str] = []
    report_date = date.today()
    _save_runner_state(
        config,
        {
            "is_running": True,
            "current_reason": reason,
            "current_report_date": report_date.isoformat(),
            "current_started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "last_error": "",
        },
    )

    try:
        if include_wechat and config.wechat.enabled:
            collected = collect_wechat_messages(config, report_date)
            if collected is not None:
                collected_sources.append("wechat")

        if include_clipboard and config.clipboard.enabled:
            try:
                collect_clipboard(config, report_date)
                collected_sources.append("clipboard")
            except RuntimeError:
                pass

        report = build_daily_report(config, report_date)
        for item in report.items:
            if item.status != "pending":
                continue
            record = ensure_note_record(config, report.report_date, item)
            updated = run_note_analysis(config, record)
            if updated.status == "completed":
                analyzed_item_ids.append(item.item_id)
            else:
                failed_item_ids.append(item.item_id)

        refreshed = build_daily_report(config, report_date)
        finished_at = datetime.now()
        result = DailyRunResult(
            report_date=refreshed.report_date,
            collected_sources=collected_sources,
            analyzed_item_ids=analyzed_item_ids,
            failed_item_ids=failed_item_ids,
            total_items=refreshed.total_items,
            completed_items=refreshed.completed_items,
            failed_items=refreshed.failed_items,
            pending_items=refreshed.pending_items,
            started_at=started_at.strftime("%Y-%m-%d %H:%M:%S"),
            finished_at=finished_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        _save_last_run(config, result, reason=reason)
        apply_retention_policy(config, today=report_date)
        notify_daily_report_ready(
            config,
            result.report_date,
            result.total_items,
            result.completed_items,
            result.failed_items,
        )
        return result
    except Exception as exc:
        _save_runner_state(
            config,
            {
                "is_running": False,
                "current_reason": "",
                "current_report_date": "",
                "current_started_at": "",
                "last_reason": reason,
                "last_report_date": report_date.isoformat(),
                "last_started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
                "last_finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_error": str(exc).strip() or exc.__class__.__name__,
            },
        )
        raise
    finally:
        _RUN_LOCK.release()


def _runner_state_path(config: AppConfig) -> Path:
    return config.paths.runtime_dir / "daily_runner_state.json"


def load_runner_state(config: AppConfig) -> dict[str, object]:
    path = _runner_state_path(config)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_runner_state(config: AppConfig, patch: dict[str, object]) -> None:
    path = _runner_state_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = load_runner_state(config)
    payload.update(patch)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _save_last_run(config: AppConfig, result: DailyRunResult, *, reason: str) -> None:
    _save_runner_state(
        config,
        {
            "is_running": False,
            "current_reason": "",
            "current_report_date": "",
            "current_started_at": "",
            "last_error": "",
            "last_reason": reason,
            "last_report_date": result.report_date,
            "last_started_at": result.started_at,
            "last_finished_at": result.finished_at,
            "last_run": asdict(result),
        },
    )
