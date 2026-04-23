from __future__ import annotations

import os
import shutil
from pathlib import Path


def resolve_ffmpeg_command(project_root: Path | None = None) -> str:
    configured = os.getenv("FFMPEG_BIN_PATH", "").strip()
    resolved = _resolve_candidate(configured)
    if resolved is not None:
        return resolved

    from_path = shutil.which("ffmpeg")
    if from_path:
        return from_path

    if project_root is not None:
        for root in _search_roots(project_root):
            discovered = _discover_under_root(root)
            if discovered is not None:
                return discovered

    return "ffmpeg"


def _resolve_candidate(value: str) -> str | None:
    if not value:
        return None
    candidate = Path(value)
    if candidate.is_dir():
        exe_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        nested = candidate / exe_name
        if nested.exists():
            return str(nested)
        return str(candidate)
    if candidate.exists():
        return str(candidate)
    return None


def _search_roots(project_root: Path) -> list[Path]:
    roots = [project_root / "tools" / "ffmpeg"]
    sibling_bilinote = project_root.parent / "BiliNote" / "tools" / "ffmpeg"
    if sibling_bilinote not in roots:
        roots.append(sibling_bilinote)
    return roots


def _discover_under_root(root: Path) -> str | None:
    if not root.exists():
        return None
    exe_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    direct = root / exe_name
    if direct.exists():
        return str(direct)
    matches = sorted(root.glob(f"**/bin/{exe_name}"))
    if matches:
        return str(matches[-1])
    return None
