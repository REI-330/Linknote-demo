from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from uuid import uuid4


def safe_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f"{path.stem}-swap-{uuid4().hex[:8]}.tmp"
    try:
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, path)
    except PermissionError:
        _powershell_write_text(path, tmp_path, content)


def safe_write_json(path: Path, payload: dict[str, object]) -> None:
    safe_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def _powershell_write_text(path: Path, tmp_path: Path, content: str) -> None:
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
