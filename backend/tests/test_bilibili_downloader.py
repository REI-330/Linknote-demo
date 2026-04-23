from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch
import shutil
import uuid

from app.downloaders.bilibili import BilibiliDownloader


class _FakeResponse:
    def __init__(self, url: str) -> None:
        self._url = url

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def geturl(self) -> str:
        return self._url


def _make_temp_dir() -> Path:
    root = Path(__file__).resolve().parents[1] / ".tmp-tests"
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"bilibili-downloader-{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_resolve_short_url_retries_get_after_head_412() -> None:
    tmp = _make_temp_dir()
    try:
        downloader = BilibiliDownloader(tmp)
        seen_methods: list[str] = []

        def fake_urlopen(request, timeout: int = 10):
            method = request.get_method()
            seen_methods.append(method)
            if method == "HEAD":
                raise HTTPError(request.full_url, 412, "Precondition Failed", hdrs=None, fp=None)
            return _FakeResponse("https://www.bilibili.com/video/BV1ab411c7mD")

        with patch("app.downloaders.bilibili.urlopen", side_effect=fake_urlopen):
            resolved = downloader._resolve_short_url("https://b23.tv/demo")

        assert resolved == "https://www.bilibili.com/video/BV1ab411c7mD"
        assert seen_methods == ["HEAD", "GET"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_extract_video_id_uses_fallback_for_blocked_short_url() -> None:
    tmp = _make_temp_dir()
    try:
        downloader = BilibiliDownloader(tmp)
        source_url = "https://b23.tv/demo"
        expected = f"short-{hashlib.sha1(source_url.encode('utf-8')).hexdigest()[:12]}"

        with patch.object(downloader, "_resolve_short_url", return_value=""):
            assert downloader._extract_video_id(source_url, allow_fallback=True) == expected
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_canonical_video_url_keeps_source_when_video_id_is_fallback() -> None:
    tmp = _make_temp_dir()
    try:
        downloader = BilibiliDownloader(tmp)
        source_url = "https://b23.tv/demo"

        assert downloader._canonical_video_url(source_url, "short-deadbeef123") == source_url
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cookie_sources_auto_detect_bilinote_cookie_file() -> None:
    tmp = _make_temp_dir()
    try:
        project_root = tmp / "linknote"
        cookie_path = tmp / "BiliNote" / "backend" / "cookies.txt"
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        cookie_path.write_text("cookie", encoding="utf-8")

        downloader = BilibiliDownloader(tmp, project_root=project_root)

        sources = downloader._cookie_sources()

        assert sources[0]["kind"] == "cookiefile"
        assert Path(sources[0]["value"]) == cookie_path
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
