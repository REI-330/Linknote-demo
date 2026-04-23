from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .prompt_templates import MERGE_PROMPT
from .prompt_builder import generate_base_prompt
from .request_chunker import RequestChunker
from ..config.settings import AnalysisConfig, ModelProviderConfig, TranscriberConfig
from ..models.media import MediaDownloadResult, TranscriptResult, TranscriptSegmentResult
from ..services.openai_client import create_openai_client


class OpenAICompatibleAnalyzer:
    def __init__(self, provider: ModelProviderConfig, api_key: str, checkpoint_dir: Path):
        self.provider = provider
        self.api_key = api_key
        self.chat_timeout = float(os.getenv("LINKNOTE_LLM_TIMEOUT_SECONDS", "180"))
        self.transcription_timeout = float(os.getenv("LINKNOTE_TRANSCRIPTION_TIMEOUT_SECONDS", "1800"))
        self.client = create_openai_client(
            api_key=api_key,
            base_url=provider.base_url,
            timeout=max(self.chat_timeout, self.transcription_timeout),
        )
        self.model = provider.default_model
        self.max_request_bytes = int(os.getenv("OPENAI_MAX_REQUEST_BYTES", str(45 * 1024 * 1024)))
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_retry_attempts = max(1, int(os.getenv("OPENAI_RETRY_ATTEMPTS", "3")))
        self.retry_base_backoff = float(os.getenv("OPENAI_RETRY_BACKOFF_SECONDS", "1.5"))

    def summarize(
        self,
        media: MediaDownloadResult,
        transcript: TranscriptResult,
        analysis_config: AnalysisConfig,
        *,
        checkpoint_key: str,
        extras: str = "",
    ) -> str:
        source_signature = self._build_source_signature(media, transcript, analysis_config, extras)
        partials = self._load_checkpoint(checkpoint_key, source_signature) or []
        formats = self._prompt_formats(analysis_config)
        chunker = RequestChunker(self._build_messages, self.max_request_bytes, self._estimate_messages_bytes)
        chunks = chunker.chunk(
            transcript.segments,
            [],
            title=media.title,
            tags=media.tags,
            format_values=formats,
            style_value=analysis_config.note_style,
            extras=extras,
        )

        if len(partials) > len(chunks):
            partials = []

        for chunk in chunks[len(partials) :]:
            messages = self._build_messages(
                chunk.segments,
                [],
                title=media.title,
                tags=media.tags,
                format_values=formats,
                style_value=analysis_config.note_style,
                extras=extras,
            )
            response = self._chat_completion_create(messages)
            partials.append(response.choices[0].message.content.strip())
            self._save_checkpoint(checkpoint_key, source_signature, partials, "summarize")

        if not partials:
            raise RuntimeError("Model returned no markdown output.")

        if len(partials) == 1:
            self._clear_checkpoint(checkpoint_key)
            return partials[0]

        merged = self._merge_partials(partials, checkpoint_key, source_signature)
        self._clear_checkpoint(checkpoint_key)
        return merged

    def answer_question(
        self,
        *,
        question: str,
        note_markdown: str,
        transcript_text: str,
        metadata: dict[str, object],
    ) -> str:
        title = str(metadata.get("title") or metadata.get("source_title") or "")
        url = str(metadata.get("canonical_url") or metadata.get("source_url") or "")
        tags = metadata.get("tags") or []
        tag_text = ", ".join(str(item) for item in tags) if isinstance(tags, list) else str(tags)
        transcript_excerpt = transcript_text[:16000]
        note_excerpt = note_markdown[:16000]
        prompt = (
            "你是 LinkNote 的单条笔记问答助手。请只基于给定笔记、原文和元信息回答。"
            "如果依据不足，要明确说明，不要编造。\n\n"
            f"标题：{title}\n"
            f"链接：{url}\n"
            f"标签：{tag_text}\n\n"
            f"AI 笔记：\n{note_excerpt}\n\n"
            f"原文参考：\n{transcript_excerpt}\n\n"
            f"用户问题：{question.strip()}\n\n"
            "请用中文作答，优先给出直接结论，必要时引用你依据的是笔记还是原文。"
        )
        response = self._chat_completion_create([{"role": "user", "content": [{"type": "text", "text": prompt}]}])
        return response.choices[0].message.content.strip()

    def chat(self, messages: list[dict[str, object]]) -> str:
        response = self._chat_completion_create(messages)
        return response.choices[0].message.content.strip()

    def transcribe(self, audio_path: str, transcriber_config: TranscriberConfig) -> TranscriptResult:
        with open(audio_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=transcriber_config.model_name,
                file=audio_file,
                response_format="verbose_json",
                language=transcriber_config.language or None,
                timeout=self.transcription_timeout,
            )

        segments: list[TranscriptSegmentResult] = []
        for segment in getattr(response, "segments", None) or []:
            segments.append(
                TranscriptSegmentResult(
                    start=float(getattr(segment, "start", 0)),
                    end=float(getattr(segment, "end", 0)),
                    text=str(getattr(segment, "text", "")).strip(),
                )
            )

        if not segments:
            text = str(getattr(response, "text", "")).strip()
            if text:
                segments = [TranscriptSegmentResult(start=0, end=0, text=text)]

        full_text = " ".join(segment.text for segment in segments).strip()
        if not full_text:
            raise RuntimeError("Transcription returned empty text.")

        return TranscriptResult(
            language=getattr(response, "language", None),
            full_text=full_text,
            segments=segments,
            raw={"source": "openai_transcription", "model_name": transcriber_config.model_name},
        )

    def _build_messages(self, segments: list, _image_urls: list[str], **kwargs) -> list[dict[str, object]]:
        segment_text = "\n".join(
            f"{self._format_time(getattr(segment, 'start', 0))} - {getattr(segment, 'text', '').strip()}"
            for segment in segments
        )
        prompt = generate_base_prompt(
            title=str(kwargs.get("title", "")),
            segment_text=segment_text,
            tags=kwargs.get("tags", []),
            format_values=kwargs.get("format_values", []),
            style_value=kwargs.get("style_value"),
            extras=kwargs.get("extras"),
        )
        return [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

    def _merge_partials(self, partials: list[str], checkpoint_key: str, source_signature: str) -> str:
        chunker = RequestChunker(lambda *_args, **_kwargs: [], self.max_request_bytes, self._estimate_messages_bytes)
        current = list(partials)
        while len(current) > 1:
            groups = chunker.group_texts_by_budget(current, self._build_merge_messages)
            next_round: list[str] = []
            for group_index, group in enumerate(groups):
                response = self._chat_completion_create(self._build_merge_messages(group))
                next_round.append(response.choices[0].message.content.strip())
                remaining = []
                for remaining_group in groups[group_index + 1 :]:
                    remaining.extend(remaining_group)
                self._save_checkpoint(checkpoint_key, source_signature, next_round + remaining, "merge")
            current = next_round
        return current[0]

    def _build_merge_messages(self, partials: list[str], **_kwargs) -> list[dict[str, object]]:
        text = MERGE_PROMPT.strip() + "\n\n" + "\n\n---\n\n".join(partials)
        return [{"role": "user", "content": [{"type": "text", "text": text}]}]

    def _chat_completion_create(self, messages: list[dict[str, object]]):
        last_exc = None
        for attempt in range(self.max_retry_attempts):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    timeout=self.chat_timeout,
                )
            except Exception as exc:
                last_exc = exc
                if attempt == self.max_retry_attempts - 1 or not self._is_retryable_error(exc):
                    raise
                time.sleep(self.retry_base_backoff * (2**attempt))
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Chat completion failed without exception.")

    def _estimate_messages_bytes(self, messages: list[dict[str, object]]) -> int:
        return len(json.dumps(messages, ensure_ascii=False).encode("utf-8"))

    def _prompt_formats(self, analysis_config: AnalysisConfig) -> list[str]:
        formats = [analysis_config.note_format] if analysis_config.note_format else []
        if analysis_config.enable_source_links and "link" not in formats:
            formats.append("link")
        if analysis_config.enable_screenshots and "screenshot" not in formats:
            formats.append("screenshot")
        return formats

    def _build_source_signature(
        self,
        media: MediaDownloadResult,
        transcript: TranscriptResult,
        analysis_config: AnalysisConfig,
        extras: str,
    ) -> str:
        payload = {
            "provider_id": self.provider.provider_id,
            "model": self.model,
            "title": media.title,
            "tags": media.tags,
            "analysis": asdict(analysis_config),
            "extras": extras,
            "segments": [asdict(segment) for segment in transcript.segments],
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _checkpoint_path(self, checkpoint_key: str) -> Path:
        safe_key = "".join(character if character.isalnum() or character in ("-", "_") else "_" for character in checkpoint_key)
        return self.checkpoint_dir / f"{safe_key}.gpt.checkpoint.json"

    def _load_checkpoint(self, checkpoint_key: str, source_signature: str) -> list[str] | None:
        path = self._checkpoint_path(checkpoint_key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            path.unlink(missing_ok=True)
            return None
        if payload.get("source_signature") != source_signature:
            path.unlink(missing_ok=True)
            return None
        partials = payload.get("partials")
        if not isinstance(partials, list):
            return None
        return [str(item) for item in partials]

    def _save_checkpoint(self, checkpoint_key: str, source_signature: str, partials: list[str], phase: str) -> None:
        path = self._checkpoint_path(checkpoint_key)
        tmp_path = path.with_suffix(".tmp")
        payload = {
            "version": 1,
            "source_signature": source_signature,
            "phase": phase,
            "partials": partials,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(path)

    def _clear_checkpoint(self, checkpoint_key: str) -> None:
        self._checkpoint_path(checkpoint_key).unlink(missing_ok=True)

    @staticmethod
    def _is_retryable_error(exc: Exception) -> bool:
        text = str(exc).lower()
        return any(
            token in text
            for token in (
                "timeout",
                "timed out",
                "rate limit",
                "429",
                "500",
                "502",
                "503",
                "504",
                "524",
                "connection error",
                "service unavailable",
            )
        )

    @staticmethod
    def _format_time(seconds: float) -> str:
        return str(timedelta(seconds=int(seconds)))[2:]
