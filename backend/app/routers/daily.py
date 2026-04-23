from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..services.config_manager import load_app_config
from ..services.daily_runner import load_runner_state, manual_run_daily
from ..services.scheduler import next_run_at


router = APIRouter(tags=["daily"])


@router.post("/daily/run")
def run_daily_now(include_wechat: bool = True, include_clipboard: bool | None = None) -> dict[str, object]:
    config = load_app_config()
    try:
        result = manual_run_daily(config, include_wechat=include_wechat, include_clipboard=include_clipboard)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "report_date": result.report_date,
        "collected_sources": result.collected_sources,
        "analyzed_item_ids": result.analyzed_item_ids,
        "failed_item_ids": result.failed_item_ids,
        "total_items": result.total_items,
        "completed_items": result.completed_items,
        "failed_items": result.failed_items,
        "pending_items": result.pending_items,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
    }


@router.get("/daily/status")
def daily_status() -> dict[str, object]:
    config = load_app_config()
    state = load_runner_state(config)
    state.update(
        {
            "schedule_enabled": config.schedule.enabled,
            "daily_time": config.schedule.daily_time,
            "auto_collect_wechat": config.schedule.auto_collect_wechat,
            "include_clipboard": config.clipboard.include_on_schedule,
            "notify_on_complete": config.schedule.notify_on_complete,
            "next_run_at": next_run_at(config),
        }
    )
    return state
