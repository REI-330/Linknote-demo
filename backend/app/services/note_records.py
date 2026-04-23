from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from ..config.settings import AppConfig
from ..models.note import NoteRecord, NoteVersion, TranscriptSegment
from ..models.report import DailyReportItem


def note_root(config: AppConfig, item_id: str) -> Path:
    return config.paths.workspace_dir / "notes" / item_id


def note_record_path(config: AppConfig, item_id: str) -> Path:
    return note_root(config, item_id) / "note.json"


def load_note_record(config: AppConfig, item_id: str) -> NoteRecord | None:
    path = note_record_path(config, item_id)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return NoteRecord(
        item_id=str(payload["item_id"]),
        report_date=str(payload["report_date"]),
        status=str(payload["status"]),
        source_url=str(payload["source_url"]),
        source_title=str(payload["source_title"]),
        source_context=str(payload["source_context"]),
        source_origins=[str(item) for item in payload.get("source_origins", [])],
        transcript_segments=[
            TranscriptSegment(
                start=float(segment.get("start", 0)),
                end=float(segment.get("end", 0)),
                text=str(segment.get("text", "")),
                speaker=str(segment.get("speaker", "")),
            )
            for segment in payload.get("transcript_segments", [])
        ],
        metadata=dict(payload.get("metadata", {})),
        analysis_progress=dict(payload.get("analysis_progress", {})),
        versions=[
            NoteVersion(
                version_id=str(version["version_id"]),
                label=str(version["label"]),
                markdown=str(version["markdown"]),
                source_basis=str(version["source_basis"]),
                created_at=str(version["created_at"]),
                model_name=str(version.get("model_name", "")),
                provider_id=str(version.get("provider_id", "")),
            )
            for version in payload.get("versions", [])
        ],
        last_error=str(payload.get("last_error", "")),
        last_error_code=str(payload.get("last_error_code", "")),
        last_error_title=str(payload.get("last_error_title", "")),
        last_error_hint=str(payload.get("last_error_hint", "")),
    )


def save_note_record(config: AppConfig, record: NoteRecord) -> Path:
    root = note_root(config, record.item_id)
    root.mkdir(parents=True, exist_ok=True)
    path = note_record_path(config, record.item_id)
    _write_json_file(path, asdict(record))
    return path


def ensure_note_record(config: AppConfig, report_date: str, item: DailyReportItem) -> NoteRecord:
    existing = load_note_record(config, item.item_id)
    if existing is not None:
        return existing
    record = NoteRecord(
        item_id=item.item_id,
        report_date=report_date,
        status="pending" if item.status == "pending" else item.status,
        source_url=item.source_url,
        source_title=item.source_title,
        source_context=item.source_context,
        source_origins=item.source_origins,
    )
    save_note_record(config, record)
    return record


def append_note_version(
    config: AppConfig,
    record: NoteRecord,
    *,
    label: str,
    markdown: str,
    source_basis: str,
    model_name: str = "",
    provider_id: str = "",
) -> NoteRecord:
    version = NoteVersion(
        version_id=uuid4().hex[:12],
        label=label,
        markdown=markdown,
        source_basis=source_basis,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        model_name=model_name,
        provider_id=provider_id,
    )
    record.versions.append(version)
    record.status = "completed"
    record.last_error = ""
    save_note_record(config, record)
    return record


def mark_note_failed(
    config: AppConfig,
    record: NoteRecord,
    message: str,
    *,
    code: str = "",
    title: str = "",
    hint: str = "",
) -> NoteRecord:
    record.status = "failed"
    record.last_error = message
    record.last_error_code = code
    record.last_error_title = title
    record.last_error_hint = hint
    save_note_record(config, record)
    return record


def reconcile_interrupted_running_notes(config: AppConfig) -> int:
    notes_dir = config.paths.workspace_dir / "notes"
    if not notes_dir.exists():
        return 0

    repaired = 0
    for path in notes_dir.glob("*/note.json"):
        try:
            record = load_note_record(config, path.parent.name)
        except Exception:
            continue
        if record is None or record.status != "running":
            continue

        record.last_error = "The previous analysis process stopped before completion."
        record.last_error_code = "analysis_interrupted"
        record.last_error_title = "上次分析已中断"
        record.last_error_hint = "后端在生成过程中重启或任务异常结束。请重新分析这条笔记。"
        record.status = "completed" if record.versions else "failed"
        save_note_record(config, record)
        repaired += 1

    return repaired


def _write_json_file(path: Path, payload: dict[str, object]) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp_path = path.parent / f"{path.stem}-swap-{uuid4().hex[:8]}.tmp"
    try:
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, path)
    except PermissionError:
        safe_path = str(path).replace("'", "''")
        safe_tmp_path = str(tmp_path).replace("'", "''")
        command = (
            "[Console]::InputEncoding=[System.Text.Encoding]::UTF8; "
            "$content = [Console]::In.ReadToEnd(); "
            f"Set-Content -LiteralPath '{safe_tmp_path}' -Value $content -Encoding UTF8; "
            f"Move-Item -LiteralPath '{safe_tmp_path}' -Destination '{safe_path}' -Force"
        )
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            input=content,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
