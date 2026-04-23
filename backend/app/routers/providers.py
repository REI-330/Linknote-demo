from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.config_manager import load_app_config
from ..services.provider_catalog import (
    add_provider,
    get_provider,
    list_providers,
    test_provider_connection,
    update_provider,
)


router = APIRouter(tags=["providers"])


class ProviderRequest(BaseModel):
    name: str
    api_key: str
    base_url: str
    logo: str | None = None
    type: str = "custom"


class ProviderUpdateRequest(BaseModel):
    id: str
    name: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    logo: str | None = None
    type: str | None = None
    enabled: int | None = None


class TestRequest(BaseModel):
    id: str


@router.get("/get_all_providers")
def get_all_providers() -> list[dict[str, object]]:
    return list_providers(load_app_config())


@router.get("/get_provider_by_id/{provider_id}")
def get_provider_by_id(provider_id: str) -> dict[str, object]:
    provider = get_provider(load_app_config(), provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider was not found.")
    return provider


@router.post("/add_provider")
def create_provider(payload: ProviderRequest) -> dict[str, object]:
    config = load_app_config()
    provider_id = add_provider(
        config,
        label=payload.name,
        api_key=payload.api_key,
        base_url=payload.base_url,
        provider_type=payload.type,
    )
    return {"id": provider_id}


@router.post("/update_provider")
def patch_provider(payload: ProviderUpdateRequest) -> dict[str, object]:
    config = load_app_config()
    provider_id = update_provider(config, payload.id, payload.model_dump())
    if provider_id is None:
        raise HTTPException(status_code=404, detail="Provider was not found.")
    return {"id": provider_id}


@router.post("/connect_test")
def connect_test(payload: TestRequest) -> dict[str, object]:
    try:
        test_provider_connection(load_app_config(), payload.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "ok"}
