from __future__ import annotations

import os
from typing import Any, Callable, TypeVar

import httpx
from openai import OpenAI

T = TypeVar("T")


def create_openai_client(*, api_key: str, base_url: str, timeout: float | None = None):
    return OpenAIClientWithDirectFallback(api_key=api_key, base_url=base_url, timeout=timeout)


def _build_openai_client(*, api_key: str, base_url: str, timeout: float | None, trust_env: bool):
    if trust_env:
        return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=0)
    http_client = httpx.Client(trust_env=False, timeout=timeout)
    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, http_client=http_client, max_retries=0)


class OpenAIClientWithDirectFallback:
    def __init__(self, *, api_key: str, base_url: str, timeout: float | None = None):
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout
        self._primary = _build_openai_client(api_key=api_key, base_url=base_url, timeout=timeout, trust_env=True)
        self._direct = None
        self.chat = _ChatNamespace(self)
        self.models = _ModelsNamespace(self)
        self.audio = _AudioNamespace(self)

    def _call_with_direct_fallback(
        self,
        operation: Callable[[Any], T],
        *,
        before_retry: Callable[[], None] | None = None,
    ) -> T:
        try:
            return operation(self._primary)
        except Exception as exc:
            if not self._should_retry_without_proxy(exc):
                raise
            if before_retry is not None:
                before_retry()
            return operation(self._direct_client)

    @property
    def _direct_client(self):
        if self._direct is None:
            self._direct = _build_openai_client(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                trust_env=False,
            )
        return self._direct

    def _should_retry_without_proxy(self, exc: Exception) -> bool:
        if not _proxy_env_present():
            return False
        for message in _exception_messages(exc):
            if any(
                token in message
                for token in (
                    "server disconnected without sending a response",
                    "remoteprotocolerror",
                    "connection error",
                    "proxy error",
                    "proxyerror",
                    "connection reset",
                    "broken pipe",
                )
            ):
                return True
        return False


class _ChatNamespace:
    def __init__(self, owner: OpenAIClientWithDirectFallback):
        self.completions = _ChatCompletionsNamespace(owner)


class _ChatCompletionsNamespace:
    def __init__(self, owner: OpenAIClientWithDirectFallback):
        self._owner = owner

    def create(self, **kwargs):
        return self._owner._call_with_direct_fallback(lambda client: client.chat.completions.create(**kwargs))


class _ModelsNamespace:
    def __init__(self, owner: OpenAIClientWithDirectFallback):
        self._owner = owner

    def list(self, **kwargs):
        return self._owner._call_with_direct_fallback(lambda client: client.models.list(**kwargs))


class _AudioNamespace:
    def __init__(self, owner: OpenAIClientWithDirectFallback):
        self.transcriptions = _AudioTranscriptionsNamespace(owner)


class _AudioTranscriptionsNamespace:
    def __init__(self, owner: OpenAIClientWithDirectFallback):
        self._owner = owner

    def create(self, **kwargs):
        file_obj = kwargs.get("file")
        initial_offset = None
        if hasattr(file_obj, "tell"):
            try:
                initial_offset = file_obj.tell()
            except Exception:
                initial_offset = None

        def _rewind_file() -> None:
            if initial_offset is None or not hasattr(file_obj, "seek"):
                return
            try:
                file_obj.seek(initial_offset)
            except Exception:
                return

        return self._owner._call_with_direct_fallback(
            lambda client: client.audio.transcriptions.create(**kwargs),
            before_retry=_rewind_file,
        )


def _proxy_env_present() -> bool:
    for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        if os.getenv(key, "").strip():
            return True
    return False


def _exception_messages(exc: Exception) -> list[str]:
    messages: list[str] = []
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        message = " ".join(str(current).strip().split()).lower()
        if message:
            messages.append(message)
        current = current.__cause__ or current.__context__
    return messages
