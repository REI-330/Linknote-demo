from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from ..config.settings import AppConfig, ensure_runtime_dirs
from ..models.report import DailyReportItem, DailyReportSummary
from .note_records import ensure_note_record, load_note_record, note_record_path
from .report_mutations import load_deleted_item_ids


URL_PATTERN = re.compile(r"https?://[^\s<>()\[\]{}\"'`]+", re.IGNORECASE)
BVID_PATTERN = re.compile(r"(BV[0-9A-Za-z]{10})", re.IGNORECASE)
TRACKING_QUERY_KEYS = {
    "spm_id_from",
    "vd_source",
    "share_source",
    "share_medium",
    "share_plat",
    "share_session_id",
    "share_tag",
    "timestamp",
    "bbid",
    "ts",
    "from",
    "seid",
    "buvid",
    "is_story_h5",
    "mid",
    "plat_id",
    "share_from",
}


def _date_dir(config: AppConfig, report_date: date) -> Path:
    return config.paths.inbox_dir / report_date.isoformat()


def _extract_bvid(url: str) -> str:
    match = BVID_PATTERN.search(url)
    return match.group(1).upper() if match else ""


def _normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=False)
        if key.lower() not in TRACKING_QUERY_KEYS
    ]
    normalized_query = urlencode(query_items, doseq=True)
    normalized_path = parsed.path.rstrip("/") or "/"
    return urlunparse(
        (
            parsed.scheme.lower() or "https",
            parsed.netloc.lower(),
            normalized_path,
            "",
            normalized_query,
            "",
        )
    )


def _dedupe_key(url: str) -> str:
    bvid = _extract_bvid(url)
    if bvid:
        return f"bvid:{bvid}"
    return f"url:{_normalize_url(url)}"


def _clean_title_from_line(line: str, url: str) -> str:
    cleaned = line.replace(url, " ").strip()
    cleaned = re.sub(r"^\[[^\]]+\]\s*", "", cleaned).strip()
    cleaned = re.sub(r"^[^:]{1,40}:\s*", "", cleaned).strip()
    return cleaned or url


def _origin_name_from_path(path: Path) -> str:
    stem = path.stem.lower()
    if "clipboard" in stem:
        return "clipboard"
    if "wechat" in stem:
        return "wechat"
    if "manual" in stem:
        return "manual"
    return "unknown"


def _note_status(config: AppConfig, item_id: str) -> tuple[str, bool, int, str, str, str]:
    path = note_record_path(config, item_id)
    if not path.exists():
        return ("pending", False, 0, "", "", "")
    record = load_note_record(config, item_id)
    if record is None:
        return ("failed", False, 0, "record_unavailable", "Record unavailable", "Unable to load note record.")
    return (
        record.status or "completed",
        True,
        len(record.versions),
        record.last_error_code,
        record.last_error_title,
        record.last_error_hint,
    )


def _line_timestamp(line: str) -> datetime | None:
    match = re.match(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", line)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _load_inbox_files(config: AppConfig, report_date: date) -> list[Path]:
    day_dir = _date_dir(config, report_date)
    if not day_dir.exists():
        return []
    return sorted(path for path in day_dir.iterdir() if path.is_file() and path.suffix.lower() == ".txt")


def build_daily_report(config: AppConfig, report_date: date) -> DailyReportSummary:
    ensure_runtime_dirs(config)
    files = _load_inbox_files(config, report_date)
    deleted_item_ids = load_deleted_item_ids(config, report_date)
    aggregated: dict[str, dict[str, object]] = {}

    for path in files:
        origin = _origin_name_from_path(path)
        for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            matches = URL_PATTERN.findall(line)
            if not matches:
                continue
            timestamp = _line_timestamp(line)
            for matched in matches:
                url = matched.rstrip(".,;:!?)】），。；：！？")
                key = _dedupe_key(url)
                collected_at = timestamp or datetime.fromtimestamp(path.stat().st_mtime)
                existing = aggregated.get(key)
                if existing is None:
                    item_id = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
                    status, has_note, versions, failure_code, failure_title, failure_hint = _note_status(config, item_id)
                    aggregated[key] = {
                        "item_id": item_id,
                        "dedupe_key": key,
                        "source_url": url,
                        "source_title": _clean_title_from_line(line, url),
                        "source_context": line,
                        "source_origins": [origin],
                        "collected_at": collected_at,
                        "status": status,
                        "has_note": has_note,
                        "failure_code": failure_code,
                        "failure_title": failure_title,
                        "failure_hint": failure_hint,
                        "versions": versions,
                    }
                    continue

                origins = set(existing["source_origins"])
                origins.add(origin)
                existing["source_origins"] = sorted(origins)
                if collected_at > existing["collected_at"]:
                    existing["collected_at"] = collected_at
                    existing["source_context"] = line

    items = [
        DailyReportItem(
            item_id=str(item["item_id"]),
            dedupe_key=str(item["dedupe_key"]),
            source_url=str(item["source_url"]),
            source_title=str(item["source_title"]),
            source_context=str(item["source_context"]),
            source_origins=list(item["source_origins"]),
            collected_at=item["collected_at"].strftime("%Y-%m-%d %H:%M:%S"),
            status=str(item["status"]),
            has_note=bool(item["has_note"]),
            failure_code=str(item.get("failure_code", "")),
            failure_title=str(item.get("failure_title", "")),
            failure_hint=str(item.get("failure_hint", "")),
            versions=int(item["versions"]),
            detail_path=f"/notes/{item['item_id']}",
        )
        for item in aggregated.values()
        if str(item["item_id"]) not in deleted_item_ids
    ]
    items.sort(key=lambda item: item.collected_at, reverse=True)

    completed = sum(1 for item in items if item.status == "completed")
    failed = sum(1 for item in items if item.status == "failed")
    pending = sum(1 for item in items if item.status in {"pending", "running"})

    return DailyReportSummary(
        report_date=report_date.isoformat(),
        total_items=len(items),
        pending_items=pending,
        completed_items=completed,
        failed_items=failed,
        items=items,
    )


def report_to_dict(report: DailyReportSummary) -> dict[str, object]:
    return asdict(report)


def note_detail_stub(config: AppConfig, item_id: str, report_date: date) -> dict[str, object]:
    report = build_daily_report(config, report_date)
    target = next((item for item in report.items if item.item_id == item_id), None)
    if target is None:
        raise KeyError(item_id)

    record = ensure_note_record(config, report.report_date, target)
    metadata = record.metadata
    progress = dict(record.analysis_progress or {})
    message = record.last_error or _analysis_message(record.status, progress)
    failure_actions_map = {
        "analysis_interrupted": ["retry"],
        "config_missing_api_key": ["settings"],
        "config_invalid_api_key": ["settings", "retry"],
        "config_missing_provider": ["settings"],
        "config_missing_model": ["settings"],
        "config_missing_transcriber_api_key": ["settings", "retry"],
        "config_missing_transcriber_provider": ["settings", "retry"],
        "transcriber_model_access_denied": ["settings", "retry"],
        "bilibili_cookies_required": ["settings", "retry", "source"],
        "bilibili_request_blocked": ["settings", "retry", "source"],
        "invalid_bilibili_url": ["source"],
        "dependency_missing_ytdlp": ["settings"],
        "dependency_missing_ffmpeg": ["settings", "retry"],
        "transcript_unavailable": ["settings", "retry", "source"],
        "analysis_failed": ["settings", "retry"],
    }

    return {
        "item": asdict(target),
        "media": {
            "platform": str(metadata.get("platform", "")),
            "video_id": str(metadata.get("video_id", "")),
            "canonical_url": str(metadata.get("canonical_url", "")),
            "cover_url": str(metadata.get("cover_url", "")),
            "duration": float(metadata.get("duration", 0) or 0),
            "uploader": str(metadata.get("uploader", "")),
            "description": str(metadata.get("description", "")),
            "transcript_source": str(metadata.get("transcript_source", "")),
            "tags": [str(tag) for tag in metadata.get("tags", [])],
        },
        "analysis": {
            "status": record.status,
            "progress": {
                "stage": str(progress.get("stage", "")),
                "step": str(progress.get("step", "")),
                "detail": str(progress.get("detail", "")),
                "started_at": str(progress.get("started_at", "")),
                "updated_at": str(progress.get("updated_at", "")),
            },
            "versions": [
                {
                    "version_id": version.version_id,
                    "label": version.label,
                    "markdown": version.markdown,
                    "source_basis": version.source_basis,
                    "created_at": version.created_at,
                    "model_name": version.model_name,
                    "provider_id": version.provider_id,
                }
                for version in reversed(record.versions)
            ],
            "view_modes": ["markdown", "mindmap"],
            "panels": {
                "source_reference": True,
                "ai_chat": True,
            },
            "message": message,
            "failure": {
                "code": record.last_error_code,
                "title": record.last_error_title or ("Analysis failed" if record.status == "failed" else ""),
                "hint": record.last_error_hint,
                "actions": failure_actions_map.get(record.last_error_code, ["retry"] if record.status == "failed" else []),
            },
            "source_reference": [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "speaker": segment.speaker,
                }
                for segment in record.transcript_segments
            ],
        },
    }


def _analysis_message(status: str, progress: dict[str, object]) -> str:
    if status == "running":
        detail = str(progress.get("detail", "")).strip()
        if detail:
            return detail
        return "Analysis is running."
    return "This note does not have an analysis result yet."
