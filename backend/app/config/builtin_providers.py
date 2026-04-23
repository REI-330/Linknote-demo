from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BuiltinProvider:
    provider_id: str
    label: str
    logo: str
    provider_type: str
    base_url: str


def _builtin_providers_path() -> Path:
    return Path(__file__).resolve().parents[1] / "db" / "builtin_providers.json"


@lru_cache(maxsize=1)
def builtin_providers() -> tuple[BuiltinProvider, ...]:
    raw = json.loads(_builtin_providers_path().read_text(encoding="utf-8"))
    return tuple(
        BuiltinProvider(
            provider_id=str(item["id"]).strip(),
            label=str(item["name"]).strip(),
            logo=str(item["logo"]).strip() or "custom",
            provider_type=str(item.get("type", "custom")).strip() or "custom",
            base_url=str(item.get("base_url", "")).strip().rstrip("/"),
        )
        for item in raw
        if str(item.get("id", "")).strip()
    )


@lru_cache(maxsize=1)
def builtin_provider_map() -> dict[str, BuiltinProvider]:
    return {provider.provider_id: provider for provider in builtin_providers()}
