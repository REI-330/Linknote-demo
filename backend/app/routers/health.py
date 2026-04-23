from __future__ import annotations

from fastapi import APIRouter

from ..services.config_manager import load_app_config
from ..services.diagnostics import collect_health_bootstrap


router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/bootstrap")
def health_bootstrap() -> dict[str, object]:
    return collect_health_bootstrap(load_app_config())
