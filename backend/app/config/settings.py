from __future__ import annotations

import json
import os
import subprocess
from uuid import uuid4
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .builtin_providers import builtin_provider_map, builtin_providers


CONFIG_FILE_NAME = "linknote.json"


@dataclass(slots=True)
class PathsConfig:
    workspace_dir: Path
    inbox_dir: Path
    reports_dir: Path
    runtime_dir: Path


@dataclass(slots=True)
class WeChatConfig:
    enabled: bool
    chatlog_root: Path
    account_dir: str
    session_allowlist: list[str]
    scan_days: int
    include_chatrooms: bool
    max_sessions: int
    max_messages_per_session: int


@dataclass(slots=True)
class ClipboardConfig:
    enabled: bool
    include_on_schedule: bool


@dataclass(slots=True)
class BilibiliConfig:
    cookies_file: str
    use_browser_cookies: bool


@dataclass(slots=True)
class ScheduleConfig:
    enabled: bool
    daily_time: str
    auto_collect_wechat: bool
    notify_on_complete: bool


@dataclass(slots=True)
class RetentionConfig:
    days: int
    cleanup_intermediate: bool


@dataclass(slots=True)
class NotificationConfig:
    enabled: bool
    open_target: str


@dataclass(slots=True)
class ServerConfig:
    host: str
    port: int
    open_browser: bool
    lan_enabled: bool


@dataclass(slots=True)
class ModelProviderConfig:
    provider_id: str
    label: str
    base_url: str
    api_key: str
    api_key_env: str
    default_model: str
    logo: str = "custom"
    type: str = "custom"
    models: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass(slots=True)
class AnalysisConfig:
    note_format: str
    note_style: str
    enable_source_links: bool
    enable_mind_map: bool
    enable_ai_chat: bool
    enable_screenshots: bool
    provider_id: str = ""
    model_name: str = ""


@dataclass(slots=True)
class TranscriberConfig:
    type: str
    provider_id: str
    model_name: str
    language: str


@dataclass(slots=True)
class AppConfig:
    project_root: Path
    paths: PathsConfig
    wechat: WeChatConfig
    clipboard: ClipboardConfig
    bilibili: BilibiliConfig
    schedule: ScheduleConfig
    retention: RetentionConfig
    notification: NotificationConfig
    server: ServerConfig
    analysis: AnalysisConfig
    transcriber: TranscriberConfig
    providers: list[ModelProviderConfig] = field(default_factory=list)


def normalize_transcriber_type(raw_type: str) -> str:
    clean_type = raw_type.strip().lower().replace("-", "_")
    if clean_type in {"builtin", "fast_whisper", "whisper"}:
        return "faster_whisper"
    if clean_type in {"openai", "openai_compatible"}:
        return "openai_compatible"
    return clean_type or "openai_compatible"


def _legacy_config_path(project_root: Path) -> Path:
    return project_root / CONFIG_FILE_NAME


def _default_provider_records() -> list[dict[str, object]]:
    return [
        {
            "provider_id": provider.provider_id,
            "label": provider.label,
            "logo": provider.logo,
            "type": provider.provider_type,
            "base_url": provider.base_url,
            "api_key": "",
            "api_key_env": "",
            "default_model": "",
            "models": [],
            "enabled": True,
        }
        for provider in builtin_providers()
    ]


def _default_raw(project_root: Path) -> dict[str, object]:
    workspace_dir = project_root / "workspace"
    return {
        "paths": {
            "workspace_dir": str(workspace_dir),
            "inbox_dir": str(workspace_dir / "inbox"),
            "reports_dir": str(workspace_dir / "reports"),
            "runtime_dir": str(workspace_dir / "runtime"),
        },
        "wechat": {
            "enabled": True,
            "chatlog_root": str(Path.home() / "chatlog"),
            "account_dir": "",
            "session_allowlist": ["filehelper", "文件传输助手"],
            "scan_days": 3,
            "include_chatrooms": False,
            "max_sessions": 20,
            "max_messages_per_session": 80,
        },
        "clipboard": {
            "enabled": True,
            "include_on_schedule": False,
        },
        "bilibili": {
            "cookies_file": "",
            "use_browser_cookies": False,
        },
        "schedule": {
            "enabled": False,
            "daily_time": "21:00",
            "auto_collect_wechat": True,
            "notify_on_complete": True,
        },
        "retention": {
            "days": 7,
            "cleanup_intermediate": True,
        },
        "notification": {
            "enabled": True,
            "open_target": "daily_report",
        },
        "server": {
            "host": "127.0.0.1",
            "port": 8765,
            "open_browser": True,
            "lan_enabled": True,
        },
        "analysis": {
            "note_format": "summary",
            "note_style": "detailed",
            "enable_source_links": True,
            "enable_mind_map": True,
            "enable_ai_chat": True,
            "enable_screenshots": False,
            "provider_id": "",
            "model_name": "",
        },
        "transcriber": {
            "type": "openai_compatible",
            "provider_id": "openai",
            "model_name": "whisper-1",
            "language": "zh",
        },
        "providers": _default_provider_records(),
    }


def _expand_path(raw_path: str, project_root: Path) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (project_root / path).resolve()


def _normalized_model_names(provider: ModelProviderConfig) -> list[str]:
    names: list[str] = []
    for model_name in provider.models:
        clean_name = str(model_name).strip()
        if clean_name and clean_name not in names:
            names.append(clean_name)
    return names


def normalize_provider_base_url(provider_id: str, base_url: str) -> str:
    clean_provider_id = provider_id.strip()
    clean_base_url = base_url.strip().rstrip("/")
    clean_base_url = _normalize_openai_compatible_base_url(clean_base_url)
    builtin = builtin_provider_map().get(clean_provider_id)
    if builtin is None:
        return clean_base_url

    canonical_base_url = builtin.base_url.strip().rstrip("/")
    if not clean_base_url:
        return canonical_base_url
    if not canonical_base_url:
        return clean_base_url

    try:
        current = urlsplit(clean_base_url)
        canonical = urlsplit(canonical_base_url)
    except ValueError:
        return clean_base_url

    if (
        current.scheme == canonical.scheme
        and current.netloc == canonical.netloc
        and current.path in ("", "/")
        and canonical.path not in ("", "/")
        and not current.query
        and not current.fragment
    ):
        return canonical_base_url
    return clean_base_url


def _normalize_openai_compatible_base_url(base_url: str) -> str:
    if not base_url:
        return ""
    try:
        parsed = urlsplit(base_url)
    except ValueError:
        return base_url

    path = parsed.path.rstrip("/")
    suffixes = (
        "/chat/completions",
        "/completions",
        "/responses",
        "/embeddings",
        "/models",
        "/audio/transcriptions",
        "/audio/speech",
    )
    for suffix in suffixes:
        if path.lower().endswith(suffix):
            trimmed = path[: -len(suffix)].rstrip("/")
            return urlunsplit((parsed.scheme, parsed.netloc, trimmed, parsed.query, parsed.fragment)).rstrip("/")
    return base_url


def _normalize_provider(provider: ModelProviderConfig) -> ModelProviderConfig:
    builtin = builtin_provider_map().get(provider.provider_id)
    default_model = provider.default_model.strip()
    models = _normalized_model_names(provider)
    if default_model and default_model not in models:
        models.insert(0, default_model)
    return ModelProviderConfig(
        provider_id=provider.provider_id.strip(),
        label=builtin.label if builtin is not None else provider.label.strip() or provider.provider_id.strip(),
        logo=builtin.logo if builtin is not None else provider.logo.strip() or "custom",
        type=builtin.provider_type if builtin is not None else provider.type.strip() or "custom",
        base_url=normalize_provider_base_url(provider.provider_id, provider.base_url),
        api_key=provider.api_key.strip(),
        api_key_env=provider.api_key_env.strip(),
        default_model=default_model,
        models=models,
        enabled=bool(provider.enabled),
    )


def _merge_builtin_providers(providers: list[ModelProviderConfig]) -> list[ModelProviderConfig]:
    normalized = [_normalize_provider(provider) for provider in providers if provider.provider_id.strip()]
    providers_by_id = {provider.provider_id: provider for provider in normalized}
    merged: list[ModelProviderConfig] = []
    builtin_ids = {provider.provider_id for provider in builtin_providers()}

    for builtin in builtin_providers():
        existing = providers_by_id.get(builtin.provider_id)
        if existing is not None:
            merged.append(existing)
            continue
        merged.append(
            ModelProviderConfig(
                provider_id=builtin.provider_id,
                label=builtin.label,
                logo=builtin.logo,
                type=builtin.provider_type,
                base_url=builtin.base_url,
                api_key="",
                api_key_env="",
                default_model="",
                models=[],
                enabled=True,
            )
        )

    for provider in normalized:
        if provider.provider_id not in builtin_ids:
            merged.append(provider)
    return merged


def config_path(project_root: Path) -> Path:
    return project_root / "workspace" / "runtime" / CONFIG_FILE_NAME


def _write_text_file(path: Path, content: str) -> None:
    tmp_path = path.parent / f"{path.stem}-swap-{uuid4().hex[:8]}.tmp"
    try:
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, path)
    except PermissionError:
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


def ensure_sample_config(project_root: Path) -> Path:
    path = config_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path
    legacy_path = _legacy_config_path(project_root)
    if legacy_path.exists():
        _write_text_file(path, legacy_path.read_text(encoding="utf-8-sig"))
        return path
    _write_text_file(path, json.dumps(_default_raw(project_root), ensure_ascii=False, indent=2))
    return path


def load_config(project_root: Path) -> AppConfig:
    root = project_root.resolve()
    raw = json.loads(config_path(root).read_text(encoding="utf-8-sig"))

    paths_raw = raw["paths"]
    wechat_raw = raw["wechat"]
    clipboard_raw = raw["clipboard"]
    bilibili_raw = raw.get("bilibili", {})
    schedule_raw = raw["schedule"]
    retention_raw = raw["retention"]
    notification_raw = raw["notification"]
    server_raw = raw["server"]
    analysis_raw = raw["analysis"]
    transcriber_raw = raw.get("transcriber", {})
    providers_raw = raw.get("providers", [])

    paths = PathsConfig(
        workspace_dir=_expand_path(str(paths_raw["workspace_dir"]), root),
        inbox_dir=_expand_path(str(paths_raw["inbox_dir"]), root),
        reports_dir=_expand_path(str(paths_raw["reports_dir"]), root),
        runtime_dir=_expand_path(str(paths_raw["runtime_dir"]), root),
    )
    wechat = WeChatConfig(
        enabled=bool(wechat_raw["enabled"]),
        chatlog_root=_expand_path(str(wechat_raw["chatlog_root"]), root),
        account_dir=str(wechat_raw["account_dir"]).strip(),
        session_allowlist=[str(item).strip() for item in wechat_raw["session_allowlist"] if str(item).strip()],
        scan_days=int(wechat_raw["scan_days"]),
        include_chatrooms=bool(wechat_raw["include_chatrooms"]),
        max_sessions=int(wechat_raw["max_sessions"]),
        max_messages_per_session=int(wechat_raw["max_messages_per_session"]),
    )
    clipboard = ClipboardConfig(
        enabled=bool(clipboard_raw["enabled"]),
        include_on_schedule=bool(clipboard_raw["include_on_schedule"]),
    )
    bilibili = BilibiliConfig(
        cookies_file=str(bilibili_raw.get("cookies_file", "")).strip(),
        use_browser_cookies=bool(bilibili_raw.get("use_browser_cookies", False)),
    )
    schedule = ScheduleConfig(
        enabled=bool(schedule_raw["enabled"]),
        daily_time=str(schedule_raw["daily_time"]).strip() or "21:00",
        auto_collect_wechat=bool(schedule_raw["auto_collect_wechat"]),
        notify_on_complete=bool(schedule_raw["notify_on_complete"]),
    )
    retention = RetentionConfig(
        days=int(retention_raw["days"]),
        cleanup_intermediate=bool(retention_raw["cleanup_intermediate"]),
    )
    notification = NotificationConfig(
        enabled=bool(notification_raw["enabled"]),
        open_target=str(notification_raw["open_target"]).strip() or "daily_report",
    )
    server = ServerConfig(
        host=str(server_raw["host"]).strip() or "127.0.0.1",
        port=max(1, int(server_raw["port"])),
        open_browser=bool(server_raw["open_browser"]),
        lan_enabled=bool(server_raw["lan_enabled"]),
    )
    analysis = AnalysisConfig(
        note_format=str(analysis_raw["note_format"]).strip() or "summary",
        note_style=str(analysis_raw["note_style"]).strip() or "detailed",
        enable_source_links=bool(analysis_raw["enable_source_links"]),
        enable_mind_map=bool(analysis_raw["enable_mind_map"]),
        enable_ai_chat=bool(analysis_raw["enable_ai_chat"]),
        enable_screenshots=bool(analysis_raw["enable_screenshots"]),
        provider_id=str(analysis_raw.get("provider_id", "")).strip(),
        model_name=str(analysis_raw.get("model_name", "")).strip(),
    )
    transcriber = TranscriberConfig(
        type=normalize_transcriber_type(str(transcriber_raw.get("type", "openai_compatible"))),
        provider_id=str(transcriber_raw.get("provider_id", "openai")).strip() or "openai",
        model_name=str(transcriber_raw.get("model_name", "whisper-1")).strip() or "whisper-1",
        language=str(transcriber_raw.get("language", "zh")).strip() or "zh",
    )
    providers = _merge_builtin_providers([
        ModelProviderConfig(
            provider_id=str(item["provider_id"]).strip(),
            label=str(item.get("label", item["provider_id"])).strip(),
            logo=str(item.get("logo", "")).strip(),
            type=str(item.get("type", "")).strip(),
            base_url=str(item["base_url"]).rstrip("/"),
            api_key=str(item.get("api_key", "")).strip(),
            api_key_env=str(item.get("api_key_env", "")).strip(),
            default_model=str(item.get("default_model", "")).strip(),
            models=[
                str(model_name).strip()
                for model_name in item.get("models", [item.get("default_model", "")])
                if str(model_name).strip()
            ],
            enabled=bool(item.get("enabled", True)),
        )
        for item in providers_raw
        if str(item.get("provider_id", "")).strip()
    ])

    return AppConfig(
        project_root=root,
        paths=paths,
        wechat=wechat,
        clipboard=clipboard,
        bilibili=bilibili,
        schedule=schedule,
        retention=retention,
        notification=notification,
        server=server,
        analysis=analysis,
        transcriber=transcriber,
        providers=providers,
    )


def ensure_runtime_dirs(config: AppConfig) -> None:
    for path in (
        config.paths.workspace_dir,
        config.paths.inbox_dir,
        config.paths.reports_dir,
        config.paths.runtime_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def dump_config(config: AppConfig) -> dict[str, object]:
    payload = asdict(config)
    payload["project_root"] = str(config.project_root)
    payload["paths"] = {
        "workspace_dir": str(config.paths.workspace_dir),
        "inbox_dir": str(config.paths.inbox_dir),
        "reports_dir": str(config.paths.reports_dir),
        "runtime_dir": str(config.paths.runtime_dir),
    }
    payload["transcriber"] = {
        "type": config.transcriber.type,
        "provider_id": config.transcriber.provider_id,
        "model_name": config.transcriber.model_name,
        "language": config.transcriber.language,
    }
    return payload


def resolve_provider_api_key(provider: ModelProviderConfig) -> str:
    if provider.api_key.strip():
        return provider.api_key.strip()
    if provider.api_key_env.strip():
        return os.getenv(provider.api_key_env, "").strip()
    return ""
