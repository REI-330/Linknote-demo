from __future__ import annotations

from dataclasses import replace
from typing import Any
from uuid import uuid4

from ..config.settings import AppConfig, ModelProviderConfig, normalize_provider_base_url, resolve_provider_api_key
from .config_manager import load_app_config, save_app_config
from .openai_client import create_openai_client


def list_providers(config: AppConfig) -> list[dict[str, Any]]:
    return [_provider_payload(provider) for provider in config.providers]


def get_provider(config: AppConfig, provider_id: str) -> dict[str, Any] | None:
    provider = _find_provider(config, provider_id)
    return _provider_payload(provider) if provider is not None else None


def add_provider(
    config: AppConfig,
    *,
    label: str,
    api_key: str,
    base_url: str,
    provider_type: str,
    enabled: bool = True,
) -> str:
    provider_id = uuid4().hex[:12]
    provider = ModelProviderConfig(
        provider_id=provider_id,
        label=label.strip(),
        logo="custom",
        type=provider_type.strip() or "custom",
        base_url=normalize_provider_base_url(provider_id, base_url),
        api_key=api_key.strip(),
        api_key_env="",
        default_model="",
        models=[],
        enabled=enabled,
    )
    config.providers.append(provider)
    _save_provider_config(config)
    return provider_id


def update_provider(config: AppConfig, provider_id: str, data: dict[str, Any]) -> str | None:
    provider = _find_provider(config, provider_id)
    if provider is None:
        return None

    next_base_url = (
        normalize_provider_base_url(provider.provider_id, str(data.get("base_url", provider.base_url)))
        or provider.base_url
    )
    reset_models = _should_reset_provider_models(provider, next_base_url)

    updated = replace(
        provider,
        label=str(data.get("name", provider.label)).strip() or provider.label,
        base_url=next_base_url,
        api_key=_resolved_api_key_value(data, provider),
        default_model="" if reset_models else provider.default_model,
        models=[] if reset_models else provider.models,
        enabled=bool(data.get("enabled", provider.enabled)),
    )
    _replace_provider(config, updated)
    _save_provider_config(config)
    return provider_id


def test_provider_connection(config: AppConfig, provider_id: str) -> None:
    provider = _find_provider(config, provider_id)
    if provider is None:
        raise RuntimeError("Provider was not found.")
    api_key = resolve_provider_api_key(provider)
    if not api_key:
        raise RuntimeError("API key is not configured.")
    try:
        client = create_openai_client(api_key=api_key, base_url=provider.base_url, timeout=10.0)
        client.models.list()
    except Exception as exc:
        raise RuntimeError(_provider_operation_error(provider, exc)) from exc


def fetch_remote_models(config: AppConfig, provider_id: str) -> dict[str, list[dict[str, Any]]]:
    provider = _find_provider(config, provider_id)
    if provider is None:
        raise RuntimeError("Provider was not found.")
    api_key = resolve_provider_api_key(provider)
    if not api_key:
        raise RuntimeError("API key is not configured.")
    try:
        client = create_openai_client(api_key=api_key, base_url=provider.base_url, timeout=15.0)
        response = client.models.list()
    except Exception as exc:
        raise RuntimeError(_provider_operation_error(provider, exc)) from exc
    return {
        "models": [
            {
                "id": str(model.id),
                "created": int(getattr(model, "created", 0) or 0),
                "object": str(getattr(model, "object", "model") or "model"),
                "owned_by": str(getattr(model, "owned_by", "") or ""),
                "permission": "",
                "root": str(getattr(model, "root", "") or ""),
            }
            for model in getattr(response, "data", []) or []
        ]
    }


def list_enabled_models(config: AppConfig) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for provider in config.providers:
        if not provider.enabled:
            continue
        names = provider.models or ([provider.default_model] if provider.default_model.strip() else [])
        for model_name in names:
            clean_name = model_name.strip()
            if not clean_name:
                continue
            items.append(
                {
                    "id": f"{provider.provider_id}:{clean_name}",
                    "provider_id": provider.provider_id,
                    "model_name": clean_name,
                }
            )
    return items


def list_enabled_models_by_provider(config: AppConfig, provider_id: str) -> list[dict[str, Any]]:
    provider = _find_provider(config, provider_id)
    if provider is None:
        return []
    names = provider.models or ([provider.default_model] if provider.default_model.strip() else [])
    return [
        {
            "id": f"{provider.provider_id}:{model_name.strip()}",
            "provider_id": provider.provider_id,
            "model_name": model_name.strip(),
        }
        for model_name in names
        if model_name.strip()
    ]


def add_enabled_model(config: AppConfig, provider_id: str, model_name: str) -> bool:
    provider = _find_provider(config, provider_id)
    if provider is None:
        raise RuntimeError("Provider was not found.")
    clean_name = model_name.strip()
    if not clean_name:
        raise RuntimeError("Model name is required.")
    names = provider.models or ([provider.default_model] if provider.default_model.strip() else [])
    if clean_name in names:
        raise RuntimeError(f"{provider.label}: model is already enabled.")
    updated_models = [*names, clean_name]
    updated = replace(
        provider,
        models=updated_models,
        default_model=provider.default_model.strip() or clean_name,
    )
    _replace_provider(config, updated)
    _save_provider_config(config)
    return True


def delete_enabled_model(config: AppConfig, model_id: str) -> bool:
    provider_id, _, model_name = model_id.partition(":")
    if not provider_id or not model_name:
        return False
    provider = _find_provider(config, provider_id)
    if provider is None:
        return False
    names = [name for name in provider.models if name.strip()]
    if model_name not in names:
        return False
    remaining = [name for name in names if name != model_name]
    updated_default = provider.default_model
    if updated_default == model_name:
        updated_default = remaining[0] if remaining else ""
    updated = replace(provider, models=remaining, default_model=updated_default)
    _replace_provider(config, updated)
    _save_provider_config(config)
    return True


def resolve_analysis_target(
    config: AppConfig,
    *,
    provider_id: str | None = None,
    model_name: str | None = None,
) -> tuple[ModelProviderConfig, str]:
    configured_provider_id = config.analysis.provider_id.strip()
    configured_model_name = config.analysis.model_name.strip()
    requested_provider_id = (provider_id or configured_provider_id).strip()
    requested_name = (model_name or configured_model_name).strip()
    if not requested_provider_id:
        raise RuntimeError("No analysis provider is configured.")

    provider = _find_provider(config, requested_provider_id)
    if provider is None or not provider.enabled:
        raise RuntimeError("Requested model provider is not enabled.")

    if not requested_name:
        raise RuntimeError("No analysis model is configured.")

    enabled_names = _configured_model_names(provider)
    if not enabled_names:
        raise RuntimeError("No configured model is available.")

    if requested_name in enabled_names:
        return provider, requested_name
    raise RuntimeError("Requested model is not enabled.")


def reconcile_analysis_target(config: AppConfig) -> None:
    provider_id = config.analysis.provider_id.strip()
    model_name = config.analysis.model_name.strip()
    if not provider_id or not model_name:
        return

    provider = _find_provider(config, provider_id)
    if provider is None or not provider.enabled:
        config.analysis = replace(config.analysis, provider_id="", model_name="")
        return

    if model_name not in _configured_model_names(provider):
        config.analysis = replace(config.analysis, provider_id="", model_name="")


def _provider_payload(provider: ModelProviderConfig) -> dict[str, Any]:
    return {
        "id": provider.provider_id,
        "provider_id": provider.provider_id,
        "name": provider.label,
        "label": provider.label,
        "logo": provider.logo,
        "type": provider.type,
        "enabled": provider.enabled,
        "base_url": provider.base_url,
        "api_key": provider.api_key,
        "api_key_env": provider.api_key_env,
        "default_model": provider.default_model,
        "models": [name for name in provider.models if name.strip()],
    }


def _save_provider_config(config: AppConfig) -> None:
    deduped: list[ModelProviderConfig] = []
    seen: set[str] = set()
    for provider in config.providers:
        if provider.provider_id in seen:
            continue
        seen.add(provider.provider_id)
        names = []
        for name in provider.models or []:
            clean_name = name.strip()
            if clean_name and clean_name not in names:
                names.append(clean_name)
        default_model = provider.default_model.strip()
        if default_model and default_model not in names:
            names.insert(0, default_model)
        deduped.append(replace(provider, models=names, default_model=default_model))
    config.providers = deduped
    reconcile_analysis_target(config)
    save_app_config(config)


def _find_provider(config: AppConfig, provider_id: str) -> ModelProviderConfig | None:
    clean_id = provider_id.strip()
    for provider in config.providers:
        if provider.provider_id == clean_id:
            return provider
    return None


def _replace_provider(config: AppConfig, updated: ModelProviderConfig) -> None:
    config.providers = [
        updated if provider.provider_id == updated.provider_id else provider
        for provider in config.providers
    ]


def _resolved_api_key_value(data: dict[str, Any], provider: ModelProviderConfig) -> str:
    if "api_key" in data:
        return str(data.get("api_key", "")).strip()
    return provider.api_key


def _should_reset_provider_models(provider: ModelProviderConfig, next_base_url: str) -> bool:
    if provider.type.strip() == "built-in":
        return False
    current_base_url = normalize_provider_base_url(provider.provider_id, provider.base_url).rstrip("/")
    return current_base_url != next_base_url.rstrip("/")


def _configured_model_names(provider: ModelProviderConfig) -> list[str]:
    names = [name.strip() for name in provider.models if name.strip()]
    default_model = provider.default_model.strip()
    if default_model and default_model not in names:
        names.insert(0, default_model)
    return names


def _provider_operation_error(provider: ModelProviderConfig, exc: Exception) -> str:
    message = " ".join(str(exc).strip().split()) or exc.__class__.__name__
    if len(message) > 180:
        message = f"{message[:177]}..."
    return f"{provider.label}: {message}"
