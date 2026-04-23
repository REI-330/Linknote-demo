from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config.settings import ensure_runtime_dirs, ensure_sample_config, load_config
from ..ingest.clipboard import collect_clipboard
from ..ingest.store import store_text_input
from ..ingest.wechat import collect_wechat_messages, list_recent_wechat_sessions
from ..ingest.wechat_refresh import refresh_wechat_export


router = APIRouter(tags=["ingest"])


def _config():
    project_root = Path(__file__).resolve().parents[3]
    ensure_sample_config(project_root)
    config = load_config(project_root)
    ensure_runtime_dirs(config)
    return config


class ManualIngestPayload(BaseModel):
    text: str
    source_name: str = "manual-link"


@router.post("/ingest/clipboard")
def ingest_clipboard() -> dict[str, str]:
    result = collect_clipboard(_config(), date.today())
    return {"path": str(result.path), "source_type": result.source_type}


@router.post("/ingest/manual")
def ingest_manual(payload: ManualIngestPayload) -> dict[str, str]:
    result = store_text_input(_config(), payload.text, payload.source_name, "manual", date.today())
    return {"path": str(result.path), "source_type": result.source_type}


@router.post("/ingest/wechat")
def ingest_wechat(force_full_scan: bool = False) -> dict[str, object]:
    try:
        result = collect_wechat_messages(_config(), date.today(), force_full_scan=force_full_scan)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "created": result is not None,
        "path": str(result.path) if result else "",
    }


@router.post("/ingest/wechat/refresh")
def refresh_wechat() -> dict[str, str]:
    try:
        path = refresh_wechat_export(_config())
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"work_dir": str(path)}


@router.get("/ingest/wechat/sessions")
def wechat_sessions(days: int | None = None) -> list[dict[str, object]]:
    try:
        sessions = list_recent_wechat_sessions(_config(), days=days)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return [
        {
            "username": session.username,
            "title": session.title,
            "last_timestamp": session.last_timestamp,
            "is_chatroom": session.is_chatroom,
        }
        for session in sessions
    ]
