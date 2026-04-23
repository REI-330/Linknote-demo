from __future__ import annotations

from datetime import date
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from app.ingest.clipboard import collect_clipboard


class DummyConfig:
    pass


def test_collect_clipboard_uses_utf8_and_stores_text() -> None:
    config = DummyConfig()
    report_date = date(2026, 4, 18)

    with patch(
        "app.ingest.clipboard.subprocess.run",
        return_value=CompletedProcess(args=[], returncode=0, stdout="hello clipboard"),
    ) as mocked_run, patch(
        "app.ingest.clipboard.store_text_input",
        return_value=type("Collected", (), {"path": Path("clipboard.txt"), "source_type": "clipboard"})(),
    ) as mocked_store:
        result = collect_clipboard(config, report_date)

    assert result.path == Path("clipboard.txt")
    mocked_store.assert_called_once_with(config, "hello clipboard", "clipboard", "clipboard", report_date)
    assert mocked_run.call_args.kwargs["encoding"] == "utf-8"
    assert mocked_run.call_args.kwargs["errors"] == "replace"

