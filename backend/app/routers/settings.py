from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..analysis import NOTE_FORMATS, NOTE_STYLES
from ..config.settings import (
    AnalysisConfig,
    BilibiliConfig,
    ClipboardConfig,
    ModelProviderConfig,
    NotificationConfig,
    RetentionConfig,
    ScheduleConfig,
    ServerConfig,
    TranscriberConfig,
    WeChatConfig,
    normalize_transcriber_type,
    normalize_provider_base_url,
)
from ..ingest.wechat_paths import list_wechat_account_options, resolve_wechat_path
from ..services.autostart import autostart_enabled, sync_autostart
from ..services.config_manager import load_app_config, save_app_config
from ..services.provider_catalog import reconcile_analysis_target


router = APIRouter(tags=["settings"])


def _config():
    return load_app_config()


class ProviderPayload(BaseModel):
    provider_id: str
    label: str
    logo: str = "custom"
    type: str = "custom"
    base_url: str
    api_key: str = ""
    api_key_env: str = ""
    default_model: str = ""
    models: list[str] = []
    enabled: bool = True


class SettingsPayload(BaseModel):
    wechat_enabled: bool
    wechat_chatlog_root: str
    wechat_account_dir: str
    wechat_scan_days: int = Field(ge=1, le=30)
    clipboard_enabled: bool
    bilibili_cookies_file: str
    bilibili_use_browser_cookies: bool
    schedule_enabled: bool
    daily_time: str
    auto_collect_wechat: bool
    notify_on_complete: bool
    clipboard_include_on_schedule: bool
    retention_days: int = Field(ge=1, le=365)
    cleanup_intermediate: bool
    note_format: str
    note_style: str
    enable_source_links: bool
    enable_mind_map: bool
    enable_ai_chat: bool
    enable_screenshots: bool
    analysis_provider_id: str = ""
    analysis_model_name: str = ""
    server_host: str
    server_port: int = Field(ge=1, le=65535)
    server_open_browser: bool
    lan_enabled: bool
    notification_enabled: bool
    notification_open_target: str
    transcriber_type: str
    transcriber_provider_id: str
    transcriber_model_name: str
    transcriber_language: str
    providers: list[ProviderPayload]


@router.get("/settings/bootstrap")
def settings_bootstrap() -> dict[str, object]:
    config = _config()
    resolved_wechat = resolve_wechat_path(config)
    wechat_root = resolved_wechat.account_root.parent if resolved_wechat is not None else config.wechat.chatlog_root
    wechat_account = resolved_wechat.account if resolved_wechat is not None else config.wechat.account_dir
    wechat_accounts = list_wechat_account_options(config)
    return {
        "note_formats": NOTE_FORMATS,
        "note_styles": NOTE_STYLES,
        "providers": [
            {
                "provider_id": provider.provider_id,
                "label": provider.label,
                "logo": provider.logo,
                "type": provider.type,
                "base_url": provider.base_url,
                "api_key": provider.api_key,
                "api_key_env": provider.api_key_env,
                "default_model": provider.default_model,
                "models": provider.models,
                "enabled": provider.enabled,
            }
            for provider in config.providers
        ],
        "schedule": {
            "enabled": config.schedule.enabled,
            "daily_time": config.schedule.daily_time,
            "auto_collect_wechat": config.schedule.auto_collect_wechat,
            "notify_on_complete": config.schedule.notify_on_complete,
            "autostart_enabled": autostart_enabled(),
        },
        "analysis": {
            "note_format": config.analysis.note_format,
            "note_style": config.analysis.note_style,
            "enable_source_links": config.analysis.enable_source_links,
            "enable_mind_map": config.analysis.enable_mind_map,
            "enable_ai_chat": config.analysis.enable_ai_chat,
            "enable_screenshots": config.analysis.enable_screenshots,
            "provider_id": config.analysis.provider_id,
            "model_name": config.analysis.model_name,
        },
        "transcriber": {
            "type": config.transcriber.type,
            "provider_id": config.transcriber.provider_id,
            "model_name": config.transcriber.model_name,
            "language": config.transcriber.language,
        },
        "retention": {
            "days": config.retention.days,
            "cleanup_intermediate": config.retention.cleanup_intermediate,
        },
        "server": {
            "host": config.server.host,
            "port": config.server.port,
            "open_browser": config.server.open_browser,
            "lan_enabled": config.server.lan_enabled,
        },
        "wechat": {
            "enabled": config.wechat.enabled,
            "chatlog_root": str(wechat_root),
            "account_dir": wechat_account,
            "scan_days": config.wechat.scan_days,
            "accounts": [
                {
                    "account_dir": option.account,
                    "chatlog_root": str(option.chatlog_root),
                    "label": option.label,
                }
                for option in wechat_accounts
            ],
        },
        "clipboard": {
            "enabled": config.clipboard.enabled,
            "include_on_schedule": config.clipboard.include_on_schedule,
        },
        "bilibili": {
            "cookies_file": config.bilibili.cookies_file,
            "use_browser_cookies": config.bilibili.use_browser_cookies,
        },
        "notification": {
            "enabled": config.notification.enabled,
            "open_target": config.notification.open_target,
        },
    }


@router.post("/settings")
def update_settings(payload: SettingsPayload) -> dict[str, object]:
    config = _config()
    config.wechat = WeChatConfig(
        enabled=payload.wechat_enabled,
        chatlog_root=Path(payload.wechat_chatlog_root.strip() or config.wechat.chatlog_root),
        account_dir=payload.wechat_account_dir.strip(),
        session_allowlist=config.wechat.session_allowlist,
        scan_days=payload.wechat_scan_days,
        include_chatrooms=config.wechat.include_chatrooms,
        max_sessions=config.wechat.max_sessions,
        max_messages_per_session=config.wechat.max_messages_per_session,
    )
    config.schedule = ScheduleConfig(
        enabled=payload.schedule_enabled,
        daily_time=payload.daily_time.strip() or "21:00",
        auto_collect_wechat=payload.auto_collect_wechat,
        notify_on_complete=payload.notify_on_complete,
    )
    config.clipboard = ClipboardConfig(
        enabled=payload.clipboard_enabled,
        include_on_schedule=payload.clipboard_include_on_schedule,
    )
    config.bilibili = BilibiliConfig(
        cookies_file=payload.bilibili_cookies_file.strip(),
        use_browser_cookies=payload.bilibili_use_browser_cookies,
    )
    config.retention = RetentionConfig(
        days=payload.retention_days,
        cleanup_intermediate=payload.cleanup_intermediate,
    )
    config.notification = NotificationConfig(
        enabled=payload.notification_enabled,
        open_target=payload.notification_open_target.strip() or "daily_report",
    )
    config.server = ServerConfig(
        host=payload.server_host.strip() or "127.0.0.1",
        port=payload.server_port,
        open_browser=payload.server_open_browser,
        lan_enabled=payload.lan_enabled,
    )
    config.analysis = AnalysisConfig(
        note_format=payload.note_format,
        note_style=payload.note_style,
        enable_source_links=payload.enable_source_links,
        enable_mind_map=payload.enable_mind_map,
        enable_ai_chat=payload.enable_ai_chat,
        enable_screenshots=payload.enable_screenshots,
        provider_id=payload.analysis_provider_id.strip(),
        model_name=payload.analysis_model_name.strip(),
    )
    config.transcriber = TranscriberConfig(
        type=normalize_transcriber_type(payload.transcriber_type),
        provider_id=payload.transcriber_provider_id.strip() or "openai",
        model_name=payload.transcriber_model_name.strip() or "whisper-1",
        language=payload.transcriber_language.strip() or "zh",
    )
    config.providers = [
        ModelProviderConfig(
            provider_id=item.provider_id.strip(),
            label=item.label.strip(),
            logo=item.logo.strip() or "custom",
            type=item.type.strip() or "custom",
            base_url=normalize_provider_base_url(item.provider_id, item.base_url),
            api_key=item.api_key.strip(),
            api_key_env=item.api_key_env.strip(),
            default_model=item.default_model.strip() or next((name.strip() for name in item.models if name.strip()), ""),
            models=[name.strip() for name in item.models if name.strip()],
            enabled=item.enabled,
        )
        for item in payload.providers
        if item.provider_id.strip() and item.base_url.strip()
    ]
    reconcile_analysis_target(config)
    try:
        save_app_config(config)
        sync_autostart(config)
    except OSError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return settings_bootstrap()
