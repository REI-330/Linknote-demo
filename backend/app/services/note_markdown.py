from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from uuid import uuid4

from .ffmpeg import resolve_ffmpeg_command


SCREENSHOT_BASE_URL = "/static/screenshots"
CONTENT_MARKER_PATTERN = re.compile(r"(?:\*?)Content-(?:\[(\d{2}):(\d{2})\]|(\d{2}):(\d{2}))")
SCREENSHOT_MARKER_PATTERN = re.compile(r"(\*?Screenshot-(?:\[(\d{2}):(\d{2})\]|(\d{2}):(\d{2})))")


def screenshot_output_dir(project_root: Path) -> Path:
    return project_root / "backend" / "static" / "screenshots"


def prepend_source_link(markdown: str, source_url: str) -> str:
    source = source_url.strip()
    if not source:
        return markdown
    header = f"> 来源链接：{source}"
    if markdown.startswith("> 来源链接："):
        return markdown
    return f"{header}\n\n{markdown}"


def replace_content_markers(markdown: str, video_url: str) -> str:
    base_url = video_url.strip()
    if not base_url:
        return markdown

    def replacer(match: re.Match[str]) -> str:
        minutes = match.group(1) or match.group(3)
        seconds = match.group(2) or match.group(4)
        total_seconds = int(minutes) * 60 + int(seconds)
        separator = "&" if "?" in base_url else "?"
        return f"[原片 @ {minutes}:{seconds}]({base_url}{separator}t={total_seconds})"

    return CONTENT_MARKER_PATTERN.sub(replacer, markdown)


def extract_screenshot_timestamps(markdown: str) -> list[tuple[str, int]]:
    matches: list[tuple[str, int]] = []
    for match in SCREENSHOT_MARKER_PATTERN.finditer(markdown):
        minutes = match.group(2) or match.group(4)
        seconds = match.group(3) or match.group(5)
        matches.append((match.group(1), int(minutes) * 60 + int(seconds)))
    return matches


def insert_screenshots(
    markdown: str,
    *,
    video_path: str,
    output_dir: Path,
    base_url: str = SCREENSHOT_BASE_URL,
) -> str:
    matches = extract_screenshot_timestamps(markdown)
    if not matches:
        return markdown

    for index, (marker, timestamp) in enumerate(matches):
        image_path = generate_screenshot(video_path, output_dir, timestamp, index)
        image_url = f"{base_url.rstrip('/')}/{image_path.name}"
        markdown = markdown.replace(marker, f"![]({image_url})", 1)
    return markdown


def generate_screenshot(video_path: str, output_dir: Path, timestamp: int, index: int) -> Path:
    ffmpeg_command = _resolve_ffmpeg_command()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"screenshot_{index:03}_{uuid4().hex[:12]}.jpg"
    command = [
        ffmpeg_command,
        "-loglevel",
        "error",
        "-ss",
        str(timestamp),
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(output_path),
        "-y",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError(f"ffmpeg executable is not available: {ffmpeg_command}") from exc
    if result.returncode != 0 or not output_path.exists():
        detail = result.stderr.strip() or result.stdout.strip() or "unknown ffmpeg error"
        raise RuntimeError(f"ffmpeg screenshot generation failed: {detail}")
    return output_path


def _resolve_ffmpeg_command() -> str:
    project_root = Path(__file__).resolve().parents[3]
    return resolve_ffmpeg_command(project_root)
