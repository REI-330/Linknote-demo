from __future__ import annotations

import importlib
import shutil
import sys
from dataclasses import dataclass


@dataclass(slots=True)
class DependencyCheck:
    module: str
    install_hint: str


REQUIRED_MODULES = [
    DependencyCheck("fastapi", "python -m pip install -e ."),
    DependencyCheck("uvicorn", "python -m pip install -e ."),
    DependencyCheck("openai", "python -m pip install -e ."),
    DependencyCheck("yt_dlp", "python -m pip install -e ."),
]


def run_checks() -> int:
    missing: list[DependencyCheck] = []
    for item in REQUIRED_MODULES:
        try:
            importlib.import_module(item.module)
        except ModuleNotFoundError:
            missing.append(item)

    if missing:
        print("[LinkNote] Missing backend dependencies:")
        for item in missing:
            print(f"  - {item.module}")
        print("[LinkNote] Install backend dependencies first:")
        print("  cd backend")
        print(f"  {missing[0].install_hint}")
        return 1

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print(f"[LinkNote] ffmpeg: {ffmpeg_path}")
    else:
        print("[LinkNote] ffmpeg not found in PATH. Public videos with native subtitles may still work.")
    return 0


def main() -> int:
    return run_checks()


if __name__ == "__main__":
    raise SystemExit(main())
