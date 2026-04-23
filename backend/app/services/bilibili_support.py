from __future__ import annotations

from pathlib import Path


def resolve_bilibili_cookie_file(project_root: Path, configured_value: str) -> Path | None:
    configured_path = _resolve_configured_cookie_path(project_root, configured_value)
    if configured_path is not None and configured_path.exists():
        return configured_path
    return discover_bilibili_cookie_file(project_root)


def describe_bilibili_cookie_source(project_root: Path, configured_value: str, use_browser_cookies: bool) -> tuple[str, str]:
    if use_browser_cookies:
        return "ok", "browser cookies enabled"

    configured_path = _resolve_configured_cookie_path(project_root, configured_value)
    if configured_path is not None:
        if configured_path.exists():
            return "ok", str(configured_path)
        discovered = discover_bilibili_cookie_file(project_root)
        if discovered is not None:
            return "ok", f"auto fallback: {discovered}"
        return "warning", str(configured_path)

    discovered = discover_bilibili_cookie_file(project_root)
    if discovered is not None:
        return "ok", f"auto fallback: {discovered}"
    return "ok", "not configured; public videos only"


def discover_bilibili_cookie_file(project_root: Path) -> Path | None:
    for candidate in _candidate_cookie_paths(project_root):
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _resolve_configured_cookie_path(project_root: Path, configured_value: str) -> Path | None:
    clean_value = configured_value.strip()
    if not clean_value:
        return None
    candidate = Path(clean_value).expanduser()
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    return candidate


def _candidate_cookie_paths(project_root: Path) -> list[Path]:
    return [
        project_root / "backend" / "cookies.txt",
        project_root / "cookies.txt",
        project_root.parent / "BiliNote" / "backend" / "cookies.txt",
    ]
