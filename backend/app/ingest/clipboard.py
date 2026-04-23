from __future__ import annotations

import subprocess
from datetime import date

from ..config.settings import AppConfig
from ..models.ingest import CollectedInput
from .store import store_text_input


def read_clipboard_text() -> str:
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def collect_clipboard(config: AppConfig, report_date: date) -> CollectedInput:
    text = read_clipboard_text()
    if not text:
        raise RuntimeError("Clipboard is empty.")
    return store_text_input(config, text, "clipboard", "clipboard", report_date)

