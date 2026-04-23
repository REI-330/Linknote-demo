from __future__ import annotations

import json
import threading
from pathlib import Path

from ..config.settings import AppConfig, config_path, dump_config, ensure_runtime_dirs, ensure_sample_config, load_config, _write_text_file

_CONFIG_LOCK = threading.RLock()


def project_root_from_here() -> Path:
    return Path(__file__).resolve().parents[3]


def load_app_config(project_root: Path | None = None) -> AppConfig:
    with _CONFIG_LOCK:
        root = project_root_from_here() if project_root is None else project_root.resolve()
        ensure_sample_config(root)
        config = load_config(root)
        ensure_runtime_dirs(config)
        return config


def save_app_config(config: AppConfig) -> Path:
    with _CONFIG_LOCK:
        path = config_path(config.project_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = dump_config(config)
        content = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
        _write_text_file(path, content)
        return path
