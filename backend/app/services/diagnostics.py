from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..config.settings import AppConfig, ModelProviderConfig, resolve_provider_api_key
from ..ingest.wechat_paths import describe_wechat_path, resolve_wechat_path
from .bilibili_support import describe_bilibili_cookie_source
from .ffmpeg import resolve_ffmpeg_command
from .openai_client import create_openai_client
from .provider_catalog import resolve_analysis_target


def _followup_for_check(key: str, status: str, detail: str, code: str) -> str:
    if key == "active_provider" and status != "ok":
        return "到设置页选择分析模型并保存，然后再重试。"
    if key == "api_key" and status != "ok":
        return "到设置页检查当前分析模型对应 provider 的 API Key。"
    if key == "provider_auth":
        if code == "invalid_api_key":
            return "当前 API Key 无效或已过期，替换后再试。"
        if code == "request_timeout":
            return "模型连通性校验超时，检查网络、代理或接口地址。"
        if code == "connection_failed":
            return "当前 provider 无法连通，检查 base URL、网络或代理。"
        if status != "ok":
            return "当前分析模型鉴权失败，回到设置页修正后再试。"
    if key == "wechat_root" and status != "ok":
        return "先修正 chatlog 路径，再使用微信采集。"
    if key == "bilibili_cookies":
        if status != "ok":
            return "检查 cookies.txt 路径，或改用浏览器 cookies fallback。"
        if "public videos only" in detail:
            return "公开视频可以直接分析；受限视频仍需 cookies。"
    return ""


def collect_health_bootstrap(config: AppConfig) -> dict[str, object]:
    frontend_dist = Path(__file__).resolve().parents[3] / "frontend" / "dist" / "index.html"
    resolved_wechat = resolve_wechat_path(config)
    bilibili_cookie_status, bilibili_cookie_detail = _bilibili_cookie_check(config)
    ffmpeg_status, ffmpeg_detail = _ffmpeg_check(config)
    active_provider, active_model_name, active_target_status, active_target_detail, active_target_code = _resolve_active_target(config)
    provider_auth = _provider_auth_check(active_provider)

    checks: list[dict[str, Any]] = [
        {
            "key": "frontend_dist",
            "label": "前端构建产物",
            "status": "ok" if frontend_dist.exists() else "warning",
            "detail": str(frontend_dist),
            "code": "ready" if frontend_dist.exists() else "missing",
        },
        {
            "key": "wechat_root",
            "label": "WeChat 数据目录",
            "status": "ok" if resolved_wechat is not None else "warning",
            "detail": describe_wechat_path(config),
            "code": "ready" if resolved_wechat is not None else "missing",
        },
        {
            "key": "active_provider",
            "label": "当前分析模型",
            "status": active_target_status,
            "detail": active_target_detail,
            "code": active_target_code,
        },
        {
            "key": "api_key",
            "label": "模型 API Key",
            "status": "ok" if active_provider and resolve_provider_api_key(active_provider) else "warning",
            "detail": _api_key_detail(active_provider, active_model_name),
            "code": "configured" if active_provider and resolve_provider_api_key(active_provider) else "missing_api_key",
        },
        provider_auth,
        {
            "key": "bilibili_cookies",
            "label": "Bilibili cookies",
            "status": bilibili_cookie_status,
            "detail": bilibili_cookie_detail,
            "code": "configured" if bilibili_cookie_status == "ok" else "missing",
        },
        {
            "key": "ffmpeg",
            "label": "FFmpeg",
            "status": ffmpeg_status,
            "detail": ffmpeg_detail,
            "code": "configured" if ffmpeg_status == "ok" else "missing",
        },
    ]

    for item in checks:
        item["followup"] = _followup_for_check(
            str(item["key"]),
            str(item["status"]),
            str(item["detail"]),
            str(item.get("code", "")),
        )

    summary_status = "ok" if all(item["status"] == "ok" for item in checks) else "warning"
    return {
        "status": summary_status,
        "checks": checks,
    }
def _bilibili_cookie_check(config: AppConfig) -> tuple[str, str]:
    return describe_bilibili_cookie_source(
        config.project_root,
        config.bilibili.cookies_file,
        config.bilibili.use_browser_cookies,
    )


def _ffmpeg_check(config: AppConfig) -> tuple[str, str]:
    command = resolve_ffmpeg_command(config.project_root)
    candidate = Path(command)
    if command == "ffmpeg" and not candidate.exists():
        return "warning", "ffmpeg not found on PATH and no bundled binary was discovered"
    return "ok", command


def _resolve_active_target(config: AppConfig) -> tuple[ModelProviderConfig | None, str, str, str, str]:
    try:
        provider, model_name = resolve_analysis_target(config)
        return provider, model_name, "ok", f"{provider.label} / {model_name}", "configured"
    except RuntimeError as exc:
        return None, "", "warning", str(exc), "missing_analysis_target"


def _provider_auth_check(provider: ModelProviderConfig | None) -> dict[str, Any]:
    if provider is None:
        return {
            "key": "provider_auth",
            "label": "模型鉴权",
            "status": "warning",
            "detail": "当前没有可校验的分析模型",
            "code": "missing_provider",
        }

    api_key = resolve_provider_api_key(provider)
    if not api_key:
        return {
            "key": "provider_auth",
            "label": "模型鉴权",
            "status": "warning",
            "detail": f"{provider.label}: API Key 未配置",
            "code": "missing_api_key",
        }

    try:
        client = create_openai_client(api_key=api_key, base_url=provider.base_url, timeout=8.0)
        client.models.list()
        return {
            "key": "provider_auth",
            "label": "模型鉴权",
            "status": "ok",
            "detail": f"{provider.label}: verified via {provider.base_url}/models",
            "code": "verified",
        }
    except Exception as exc:
        code, detail = _classify_provider_error(exc, provider)
        return {
            "key": "provider_auth",
            "label": "模型鉴权",
            "status": "warning",
            "detail": detail,
            "code": code,
        }


def _classify_provider_error(exc: Exception, provider: ModelProviderConfig) -> tuple[str, str]:
    message = _compact_error_message(str(exc))
    lower = message.lower()

    if any(token in lower for token in ("incorrect api key", "invalid_api_key", "invalid api key", "401", "unauthorized")):
        return "invalid_api_key", f"{provider.label}: API Key invalid or expired"
    if any(token in lower for token in ("timeout", "timed out", "deadline exceeded")):
        return "request_timeout", f"{provider.label}: provider verification timed out"
    if any(token in lower for token in ("connection", "dns", "name or service not known", "nodename nor servname")):
        return "connection_failed", f"{provider.label}: unable to reach {provider.base_url}"
    return "verification_failed", f"{provider.label}: {message}"


def _compact_error_message(message: str) -> str:
    normalized = " ".join(message.strip().split())
    if len(normalized) <= 180:
        return normalized
    return normalized[:177] + "..."


def _api_key_detail(provider: ModelProviderConfig | None, model_name: str = "") -> str:
    if provider is None:
        return "当前还没有在设置页选定分析模型。"
    target_label = f"{provider.label} / {model_name}" if model_name else provider.label
    if provider.api_key.strip():
        return f"{target_label}: API Key 已保存在设置中"
    if provider.api_key_env.strip() and os.getenv(provider.api_key_env, "").strip():
        return f"{target_label}: 来自环境变量 {provider.api_key_env}"
    if provider.api_key_env.strip():
        return f"{target_label}: 设置内为空，环境变量 {provider.api_key_env} 也不可用"
    return f"{target_label}: API Key 为空"
