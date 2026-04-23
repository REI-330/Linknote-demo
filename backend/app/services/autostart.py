from __future__ import annotations

import os
from pathlib import Path

from ..config.settings import AppConfig, _write_text_file


AUTOSTART_FILE_NAME = "LinkNote-Autostart.cmd"


def autostart_script_path() -> Path:
    appdata = os.getenv("APPDATA", "").strip()
    base = Path(appdata) if appdata else (Path.home() / "AppData" / "Roaming")
    return base / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / AUTOSTART_FILE_NAME


def autostart_enabled() -> bool:
    return autostart_script_path().exists()


def sync_autostart(config: AppConfig) -> Path | None:
    path = autostart_script_path()
    if not config.schedule.enabled:
        if path.exists():
            path.unlink()
        return None

    path.parent.mkdir(parents=True, exist_ok=True)
    _write_text_file(path, _autostart_script(config))
    return path


def _autostart_script(config: AppConfig) -> str:
    backend_dir = str((config.project_root / "backend").resolve())
    safe_backend_dir = backend_dir.replace('"', '""')
    safe_port = str(config.server.port)
    return (
        "@echo off\r\n"
        "setlocal\r\n"
        f'netstat -ano | findstr /r /c:":{safe_port} .*LISTENING" >nul 2>nul\r\n'
        "if %errorlevel%==0 exit /b 0\r\n"
        f'start "LinkNote" /min cmd /c "cd /d ""{safe_backend_dir}"" && set LINKNOTE_SUPPRESS_BROWSER=1 && python -m app.run_local"\r\n'
        "endlocal\r\n"
    )
