from __future__ import annotations

"""FastAPI application entrypoint for the packaged local LinkNote app."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers.daily import router as daily_router
from .routers.health import router as health_router
from .routers.ingest import router as ingest_router
from .routers.models import router as models_router
from .routers.providers import router as providers_router
from .routers.reports import router as reports_router
from .routers.settings import router as settings_router
from .services.autostart import sync_autostart
from .services.config_manager import load_app_config
from .services.note_markdown import screenshot_output_dir
from .services.note_records import reconcile_interrupted_running_notes
from .services.scheduler import DailyScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup work is centralized here so local runs and packaged runs share
    # the same recovery and scheduler behavior.
    config = load_app_config()
    sync_autostart(config)
    reconcile_interrupted_running_notes(config)
    scheduler = DailyScheduler(load_app_config)
    scheduler.start()
    app.state.daily_scheduler = scheduler
    try:
        yield
    finally:
        scheduler.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="LinkNote", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(daily_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(ingest_router, prefix="/api")
    app.include_router(providers_router, prefix="/api")
    app.include_router(models_router, prefix="/api")
    app.include_router(reports_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    # Screenshots are served as static assets because note markdown may embed
    # generated local image URLs after post-processing.
    screenshot_dir = screenshot_output_dir(load_app_config().project_root)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static/screenshots", StaticFiles(directory=screenshot_dir), name="screenshots")
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    return app


app = create_app()
