from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .base import Downloader
from ..models.media import MediaDownloadResult, TranscriptResult, TranscriptSegmentResult
from ..services.bilibili_support import resolve_bilibili_cookie_file


logger = logging.getLogger(__name__)

BVID_PATTERN = re.compile(r"(BV[0-9A-Za-z]{10})", re.IGNORECASE)
SHORT_LINK_HOSTS = {"b23.tv", "www.b23.tv"}
SHORT_LINK_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://www.bilibili.com/",
}

try:
    import yt_dlp
except ModuleNotFoundError:  # pragma: no cover - runtime dependency gate
    yt_dlp = None


class BilibiliDownloader(Downloader):
    def __init__(
        self,
        cache_dir: Path,
        *,
        project_root: Path | None = None,
        ffmpeg_location: str = "",
        cookies_file: str = "",
        use_browser_cookies: bool = False,
    ):
        super().__init__(cache_dir)
        self.project_root = project_root
        self.ffmpeg_location = ffmpeg_location.strip()
        self.cookies_file = cookies_file.strip()
        self.use_browser_cookies = use_browser_cookies
        self.temp_dir = self.cache_dir / ".tmp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def fetch_media(self, source_url: str, *, download_audio: bool, download_video: bool = False) -> MediaDownloadResult:
        self._ensure_dependency()
        video_id = self._extract_video_id(source_url, allow_fallback=True)
        info = self._extract_info_with_cookie_fallback(
            self._apply_common_opts(
                {
                    "noplaylist": True,
                    "quiet": True,
                    "skip_download": True,
                    "outtmpl": str(self.cache_dir / "%(id)s.%(ext)s"),
                }
            ),
            source_url,
            download=False,
        )
        audio_path = ""
        video_path = ""
        if download_audio:
            audio_info = self._download_audio(source_url)
            audio_path = self._resolve_downloaded_audio_path(audio_info, video_id)
            info = audio_info
        if download_video:
            video_info = self._download_video(source_url)
            video_path = self._resolve_downloaded_video_path(video_info, video_id)
            info = video_info if not download_audio else info
        resolved_video_id = str(info.get("id") or video_id)
        canonical_url = self._canonical_video_url(info.get("webpage_url") or source_url, resolved_video_id)
        description = str(info.get("description") or "")
        uploader = str(info.get("uploader") or info.get("channel") or "")
        tags = [str(tag) for tag in info.get("tags") or [] if str(tag).strip()]
        duration = float(info.get("duration") or 0)
        return MediaDownloadResult(
            source_url=source_url,
            canonical_url=canonical_url,
            platform="bilibili",
            video_id=resolved_video_id,
            title=str(info.get("title") or source_url),
            duration=duration,
            cover_url=str(info.get("thumbnail") or ""),
            description=description,
            uploader=uploader,
            tags=tags,
            audio_path=audio_path if Path(audio_path).exists() or not download_audio else "",
            video_path=video_path if Path(video_path).exists() or not download_video else "",
            raw_info=self._json_safe(info),
        )

    def fetch_subtitles(self, source_url: str) -> TranscriptResult | None:
        self._ensure_dependency()
        video_id = self._extract_video_id(source_url, allow_fallback=True)
        langs = ["zh-Hans", "zh", "zh-CN", "ai-zh", "en", "en-US"]
        ydl_opts: dict[str, Any] = {
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": langs,
            "subtitlesformat": "srt/json3/best",
            "skip_download": True,
            "quiet": True,
            "outtmpl": str(self.cache_dir / f"{video_id}.%(ext)s"),
        }
        ydl_opts = self._apply_common_opts(ydl_opts)
        try:
            info = self._extract_info_with_cookie_fallback(ydl_opts, source_url, download=True)
        except Exception as exc:
            logger.warning("Bilibili subtitle fetch failed: %s", exc)
            return None

        subtitles = info.get("requested_subtitles") or {}
        if not subtitles:
            return None

        detected_lang = ""
        subtitle_info: dict[str, Any] | None = None
        for lang in langs:
            if lang in subtitles:
                detected_lang = lang
                subtitle_info = subtitles[lang]
                break
        if subtitle_info is None:
            for lang, candidate in subtitles.items():
                if lang != "danmaku":
                    detected_lang = str(lang)
                    subtitle_info = candidate
                    break
        if subtitle_info is None:
            return None

        data = subtitle_info.get("data")
        if isinstance(data, str) and data.strip():
            return self._parse_srt_content(data, detected_lang, source_url)

        ext = subtitle_info.get("ext", "srt")
        subtitle_path = self.cache_dir / f"{video_id}.{detected_lang}.{ext}"
        if not subtitle_path.exists():
            return None
        if ext == "json3":
            return self._parse_json3_file(subtitle_path, detected_lang, source_url)
        return self._parse_srt_content(subtitle_path.read_text(encoding="utf-8"), detected_lang, source_url)

    def _ensure_dependency(self) -> None:
        if yt_dlp is None:
            raise RuntimeError("yt-dlp is not installed. Run `python -m pip install yt-dlp` in the backend environment.")

    def _apply_common_opts(self, options: dict[str, Any]) -> dict[str, Any]:
        prepared = dict(options)
        if self.ffmpeg_location:
            prepared["ffmpeg_location"] = self.ffmpeg_location
        for source in self._cookie_sources():
            if source["kind"] == "cookiefile":
                prepared["cookiefile"] = source["value"]
                break
        return prepared

    def _cookie_sources(self) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []
        project_root = self.project_root or Path(__file__).resolve().parents[3]
        cookies_path = resolve_bilibili_cookie_file(project_root, self.cookies_file)
        if cookies_path is not None:
            sources.append({"kind": "cookiefile", "value": str(cookies_path), "label": f"file:{cookies_path}"})
        if self.use_browser_cookies or os.getenv("LINKNOTE_USE_BROWSER_COOKIES", "").strip().lower() in {"1", "true", "yes"}:
            browser_roots = {
                "edge": Path(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")),
                "chrome": Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")),
                "brave": Path(os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data")),
                "chromium": Path(os.path.expandvars(r"%LOCALAPPDATA%\Chromium\User Data")),
                "firefox": Path(os.path.expandvars(r"%APPDATA%\Mozilla\Firefox")),
            }
            for browser, browser_root in browser_roots.items():
                if browser_root.exists():
                    sources.append({"kind": "browser", "value": (browser,), "label": f"browser:{browser}"})
        return sources

    def _extract_info_with_cookie_fallback(self, options: dict[str, Any], source_url: str, *, download: bool) -> dict[str, Any]:
        sources: list[dict[str, Any] | None] = [None, *self._cookie_sources()]
        errors: list[str] = []
        original_tmp = os.environ.get("TMP", "")
        original_temp = os.environ.get("TEMP", "")
        os.environ["TMP"] = str(self.temp_dir)
        os.environ["TEMP"] = str(self.temp_dir)
        try:
            for source in sources:
                current = dict(options)
                if source is not None and source["kind"] == "browser":
                    current["cookiesfrombrowser"] = source["value"]
                if source is not None and source["kind"] == "cookiefile":
                    current["cookiefile"] = source["value"]
                try:
                    with yt_dlp.YoutubeDL(current) as ydl:
                        return ydl.extract_info(source_url, download=download)
                except Exception as exc:
                    errors.append(f"{source['label'] if source else 'no-cookies'}: {exc}")
                    continue
        finally:
            if original_tmp:
                os.environ["TMP"] = original_tmp
            else:
                os.environ.pop("TMP", None)
            if original_temp:
                os.environ["TEMP"] = original_temp
            else:
                os.environ.pop("TEMP", None)
        raise RuntimeError("No usable Bilibili cookie source was available. " + " | ".join(errors))

    def _download_audio(self, source_url: str) -> dict[str, Any]:
        options = self._apply_common_opts(
            {
                "noplaylist": True,
                "quiet": True,
                "skip_download": False,
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "outtmpl": str(self.cache_dir / "%(id)s.%(ext)s"),
            }
        )
        return self._extract_info_with_cookie_fallback(options, source_url, download=True)

    def _download_video(self, source_url: str) -> dict[str, Any]:
        options = self._apply_common_opts(
            {
                "noplaylist": True,
                "quiet": True,
                "skip_download": False,
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
                "outtmpl": str(self.cache_dir / "%(id)s.%(ext)s"),
            }
        )
        return self._extract_info_with_cookie_fallback(options, source_url, download=True)

    def _extract_video_id(self, source_url: str, *, allow_fallback: bool = False) -> str:
        match = BVID_PATTERN.search(source_url)
        if match:
            return match.group(1).upper()
        if self._is_short_bilibili_url(source_url):
            resolved = self._resolve_short_url(source_url)
            if resolved:
                match = BVID_PATTERN.search(resolved)
                if match:
                    return match.group(1).upper()
            if allow_fallback:
                return self._fallback_video_id(source_url)
        raise RuntimeError("Unable to extract BV id from Bilibili url.")

    def _resolve_short_url(self, source_url: str) -> str:
        for method in ("HEAD", "GET"):
            request = Request(source_url, method=method, headers=SHORT_LINK_HEADERS)
            try:
                with urlopen(request, timeout=10) as response:  # noqa: S310
                    return response.geturl()
            except HTTPError as exc:
                if method == "HEAD" and exc.code in {405, 412}:
                    logger.info("Short link resolution blocked via HEAD (%s), retrying GET: %s", exc.code, source_url)
                    continue
                logger.warning("Failed to resolve Bilibili short link via %s: %s (%s)", method, source_url, exc)
                return ""
            except URLError as exc:
                logger.warning("Failed to resolve Bilibili short link via %s: %s (%s)", method, source_url, exc)
                return ""
        return ""

    def _canonical_video_url(self, source_url: str, video_id: str) -> str:
        parsed = urlparse(source_url)
        if parsed.netloc.lower().endswith("bilibili.com") and parsed.path:
            return source_url
        if not BVID_PATTERN.fullmatch(video_id):
            return source_url
        return f"https://www.bilibili.com/video/{video_id}"

    def _fallback_video_id(self, source_url: str) -> str:
        digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:12]
        return f"short-{digest}"

    def _is_short_bilibili_url(self, source_url: str) -> bool:
        return urlparse(source_url).netloc.lower() in SHORT_LINK_HOSTS

    def _parse_srt_content(self, srt_content: str, language: str, source_url: str) -> TranscriptResult | None:
        pattern = re.compile(
            r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n\d+\n|$)",
            re.DOTALL,
        )
        segments: list[TranscriptSegmentResult] = []
        for _index, start_time, end_time, text in pattern.findall(srt_content):
            normalized = text.strip()
            if not normalized:
                continue
            segments.append(
                TranscriptSegmentResult(
                    start=self._time_to_seconds(start_time),
                    end=self._time_to_seconds(end_time),
                    text=normalized,
                )
            )
        if not segments:
            return None
        return TranscriptResult(
            language=language,
            full_text=" ".join(segment.text for segment in segments),
            segments=segments,
            raw={"source": "bilibili_subtitle", "format": "srt", "source_url": source_url},
        )

    def _parse_json3_file(self, subtitle_path: Path, language: str, source_url: str) -> TranscriptResult | None:
        data = json.loads(subtitle_path.read_text(encoding="utf-8"))
        segments: list[TranscriptSegmentResult] = []
        for event in data.get("events") or []:
            text = "".join(str(part.get("utf8", "")) for part in event.get("segs") or []).strip()
            if not text:
                continue
            start_ms = int(event.get("tStartMs") or 0)
            duration_ms = int(event.get("dDurationMs") or 0)
            segments.append(
                TranscriptSegmentResult(
                    start=start_ms / 1000.0,
                    end=(start_ms + duration_ms) / 1000.0,
                    text=text,
                )
            )
        if not segments:
            return None
        return TranscriptResult(
            language=language,
            full_text=" ".join(segment.text for segment in segments),
            segments=segments,
            raw={
                "source": "bilibili_subtitle",
                "format": "json3",
                "subtitle_path": str(subtitle_path),
                "source_url": source_url,
            },
        )

    @staticmethod
    def _time_to_seconds(value: str) -> float:
        hours, minutes, seconds = value.replace(",", ".").split(":")
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)

    def _resolve_downloaded_audio_path(self, info: dict[str, Any], video_id: str) -> str:
        candidates: list[Path] = []

        filepath = info.get("filepath")
        if isinstance(filepath, str) and filepath.strip():
            candidates.append(Path(filepath))

        for item in info.get("requested_downloads") or []:
            if not isinstance(item, dict):
                continue
            candidate_path = item.get("filepath")
            if isinstance(candidate_path, str) and candidate_path.strip():
                candidates.append(Path(candidate_path))

        requested_formats = info.get("requested_formats") or []
        for item in requested_formats:
            if not isinstance(item, dict):
                continue
            candidate_path = item.get("filepath")
            if isinstance(candidate_path, str) and candidate_path.strip():
                candidates.append(Path(candidate_path))

        info_ext = str(info.get("ext") or "").strip()
        if info_ext:
            candidates.append(self.cache_dir / f"{info.get('id', video_id)}.{info_ext}")

        for extension in ("m4a", "webm", "mp3", "mp4", "m4s"):
            candidates.append(self.cache_dir / f"{info.get('id', video_id)}.{extension}")

        for candidate in candidates:
            resolved = candidate if candidate.is_absolute() else (self.cache_dir / candidate).resolve()
            if resolved.exists() and resolved.is_file():
                return str(resolved)
        return ""

    def _resolve_downloaded_video_path(self, info: dict[str, Any], video_id: str) -> str:
        candidates: list[Path] = []

        filepath = info.get("filepath")
        if isinstance(filepath, str) and filepath.strip():
            candidates.append(Path(filepath))

        for item in info.get("requested_downloads") or []:
            if not isinstance(item, dict):
                continue
            candidate_path = item.get("filepath")
            if isinstance(candidate_path, str) and candidate_path.strip():
                candidates.append(Path(candidate_path))

        requested_formats = info.get("requested_formats") or []
        for item in requested_formats:
            if not isinstance(item, dict):
                continue
            candidate_path = item.get("filepath")
            if isinstance(candidate_path, str) and candidate_path.strip():
                candidates.append(Path(candidate_path))

        info_ext = str(info.get("ext") or "").strip()
        if info_ext:
            candidates.append(self.cache_dir / f"{info.get('id', video_id)}.{info_ext}")

        for extension in ("mp4", "mkv", "webm", "flv", "mov"):
            candidates.append(self.cache_dir / f"{info.get('id', video_id)}.{extension}")

        for candidate in candidates:
            resolved = candidate if candidate.is_absolute() else (self.cache_dir / candidate).resolve()
            if resolved.exists() and resolved.is_file():
                return str(resolved)
        return ""

    @staticmethod
    def _json_safe(payload: dict[str, Any]) -> dict[str, Any]:
        return json.loads(json.dumps(payload, ensure_ascii=False, default=str))
