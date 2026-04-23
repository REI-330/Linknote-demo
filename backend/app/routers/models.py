from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.config_manager import load_app_config
from ..services.provider_catalog import (
    add_enabled_model,
    delete_enabled_model,
    fetch_remote_models,
    list_enabled_models,
    list_enabled_models_by_provider,
)


router = APIRouter(tags=["models"])


class CreateModelRequest(BaseModel):
    provider_id: str
    model_name: str


@router.get("/model_list")
def model_list() -> list[dict[str, object]]:
    return list_enabled_models(load_app_config())


@router.get("/model_list/{provider_id}")
def remote_model_list(provider_id: str) -> dict[str, object]:
    try:
        return fetch_remote_models(load_app_config(), provider_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/model_enable/{provider_id}")
def enabled_model_list(provider_id: str) -> list[dict[str, object]]:
    return list_enabled_models_by_provider(load_app_config(), provider_id)


@router.post("/models")
def create_model(payload: CreateModelRequest) -> dict[str, object]:
    config = load_app_config()
    clean_name = payload.model_name.strip()
    try:
        add_enabled_model(config, payload.provider_id, clean_name)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    created_model = next(
        (
            model
            for model in list_enabled_models_by_provider(config, payload.provider_id)
            if str(model.get("model_name", "")).strip() == clean_name
        ),
        None,
    )
    return {
        "status": "ok",
        "model": created_model
        or {
            "id": f"{payload.provider_id}:{clean_name}",
            "provider_id": payload.provider_id,
            "model_name": clean_name,
        },
    }


@router.get("/models/delete/{model_id}")
def remove_model(model_id: str) -> dict[str, object]:
    removed = delete_enabled_model(load_app_config(), model_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Model was not found.")
    return {"status": "ok"}
