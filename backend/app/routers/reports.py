from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from ..config.settings import AppConfig
from ..config.settings import ensure_runtime_dirs, ensure_sample_config, load_config
from ..models.note import NoteRecord
from ..services.note_chat import answer_note_question
from ..services.note_generation import run_note_analysis
from ..services.note_records import ensure_note_record, load_note_record
from ..services.report_index import build_daily_report, note_detail_stub, report_to_dict
from ..services.report_mutations import delete_failed_report_item


router = APIRouter(tags=["reports"])


def _config():
    project_root = Path(__file__).resolve().parents[3]
    ensure_sample_config(project_root)
    config = load_config(project_root)
    ensure_runtime_dirs(config)
    return config


@router.get("/reports/today")
def today_report() -> dict[str, object]:
    return report_to_dict(build_daily_report(_config(), date.today()))


@router.get("/reports/{report_date}")
def report_by_date(report_date: str) -> dict[str, object]:
    try:
        parsed = date.fromisoformat(report_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid report date.") from exc
    return report_to_dict(build_daily_report(_config(), parsed))


@router.get("/notes/{item_id}")
def note_detail(item_id: str, report_date: str | None = None) -> dict[str, object]:
    try:
        parsed_date = date.today() if not report_date else date.fromisoformat(report_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid report date.") from exc
    try:
        return note_detail_stub(_config(), item_id, parsed_date)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Note was not found.") from exc


@router.post("/notes/{item_id}/analyze")
def analyze_note(item_id: str, payload: dict[str, object] | None = None, report_date: str | None = None) -> dict[str, object]:
    return _run_analysis(item_id, report_date, allow_existing=False, payload=payload or {})


@router.post("/notes/{item_id}/reanalyze")
def reanalyze_note(item_id: str, payload: dict[str, object] | None = None, report_date: str | None = None) -> dict[str, object]:
    return _run_analysis(item_id, report_date, allow_existing=True, payload=payload or {})


@router.delete("/reports/{report_date}/items/{item_id}")
def delete_report_item(report_date: str, item_id: str) -> dict[str, object]:
    try:
        parsed = date.fromisoformat(report_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid report date.") from exc

    try:
        delete_failed_report_item(_config(), item_id, parsed)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Note was not found.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"deleted": True, "item_id": item_id}


@router.get("/notes/{item_id}/export", response_class=PlainTextResponse)
def export_note_markdown(item_id: str, report_date: str | None = None) -> PlainTextResponse:
    config, record = _resolve_note_record(item_id, report_date)
    if not record.versions:
        raise HTTPException(status_code=409, detail="This note does not have an analysis result yet.")
    latest = record.versions[-1]
    filename = f"{item_id}.md"
    return PlainTextResponse(
        latest.markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/notes/{item_id}/chat")
def note_chat(item_id: str, payload: dict[str, object], report_date: str | None = None) -> dict[str, object]:
    config, record = _resolve_note_record(item_id, report_date)
    question = str(payload.get("question", "")).strip()
    history_raw = payload.get("history")
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")
    history: list[dict[str, str]] = []
    if isinstance(history_raw, list):
        for item in history_raw:
            if not isinstance(item, dict):
                continue
            history.append(
                {
                    "role": str(item.get("role", "")).strip(),
                    "content": str(item.get("content", "")).strip(),
                }
            )
    try:
        answer, sources = answer_note_question(
            config,
            record,
            question,
            history,
            provider_id=str(payload.get("provider_id", "")).strip() or None,
            model_name=str(payload.get("model_name", "")).strip() or None,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"answer": answer, "sources": sources}


def _run_analysis(
    item_id: str,
    report_date: str | None,
    *,
    allow_existing: bool,
    payload: dict[str, object],
) -> dict[str, object]:
    config, record = _resolve_note_record(item_id, report_date)
    if record.versions and not allow_existing:
        return {"status": record.status, "versions": len(record.versions)}

    updated = run_note_analysis(
        config,
        record,
        provider_id=str(payload.get("provider_id", "")).strip() or None,
        model_name=str(payload.get("model_name", "")).strip() or None,
    )
    return {"status": updated.status, "versions": len(updated.versions)}


def _resolve_note_record(item_id: str, report_date: str | None) -> tuple[AppConfig, NoteRecord]:
    try:
        parsed_date = date.today() if not report_date else date.fromisoformat(report_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid report date.") from exc

    config = _config()
    report = build_daily_report(config, parsed_date)
    target = next((item for item in report.items if item.item_id == item_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Note was not found.")
    record = load_note_record(config, item_id) or ensure_note_record(config, report.report_date, target)
    return config, record
