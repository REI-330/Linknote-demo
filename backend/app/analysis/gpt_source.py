from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class GPTSource:
    segment: list[Any]
    title: str
    tags: list[str] | str
    screenshot: bool = False
    link: bool = False
    style: str | None = None
    extras: str | None = None
    _format: list[str] | None = None
    video_img_urls: list[str] | None = None
    checkpoint_key: str | None = None
