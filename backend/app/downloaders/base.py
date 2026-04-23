from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..models.media import MediaDownloadResult, TranscriptResult


class Downloader(ABC):
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def fetch_media(self, source_url: str, *, download_audio: bool, download_video: bool = False) -> MediaDownloadResult:
        raise NotImplementedError

    @abstractmethod
    def fetch_subtitles(self, source_url: str) -> TranscriptResult | None:
        raise NotImplementedError
