from __future__ import annotations

import subprocess
from pathlib import Path

from ..config.settings import AppConfig
from .wechat_paths import load_chatlog_history_entry


def _default_chatlog_alpha_source() -> Path:
    return Path.home() / "chatlog-alpha-src"


def refresh_wechat_export(config: AppConfig, source_root: Path | None = None) -> Path:
    entry = load_chatlog_history_entry(config)
    alpha_source = source_root or _default_chatlog_alpha_source()
    if not alpha_source.exists():
        raise RuntimeError(f"chatlog-alpha-src was not found: {alpha_source}")

    command = [
        "go",
        "run",
        ".",
        "decrypt",
        "-d",
        str(entry.data_dir),
        "-w",
        str(entry.work_dir),
        "-p",
        entry.platform,
        "-v",
        str(entry.version),
        "-k",
        entry.data_key,
    ]
    completed = subprocess.run(
        command,
        cwd=alpha_source,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = completed.stdout.strip()
    if output:
        print(output)
    return entry.work_dir


def maybe_refresh_wechat_export(config: AppConfig, source_root: Path | None = None) -> Path | None:
    try:
        return refresh_wechat_export(config, source_root=source_root)
    except Exception:
        return None
