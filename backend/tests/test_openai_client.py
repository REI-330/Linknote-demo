from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import httpx

from app.services.openai_client import create_openai_client


def _remote_protocol_exception() -> Exception:
    try:
        raise httpx.RemoteProtocolError("Server disconnected without sending a response.")
    except httpx.RemoteProtocolError as cause:
        try:
            raise RuntimeError("Connection error.") from cause
        except RuntimeError as exc:
            return exc


class _FakeModels:
    def __init__(self, *, value=None, exc: Exception | None = None):
        self._value = value
        self._exc = exc

    def list(self, **_kwargs):
        if self._exc is not None:
            raise self._exc
        return self._value


class _FakeChatCompletions:
    def __init__(self, *, value=None, exc: Exception | None = None):
        self._value = value
        self._exc = exc

    def create(self, **_kwargs):
        if self._exc is not None:
            raise self._exc
        return self._value


class _FakeChat:
    def __init__(self, *, value=None, exc: Exception | None = None):
        self.completions = _FakeChatCompletions(value=value, exc=exc)


class _FakeAudioTranscriptions:
    def __init__(self, *, value=None, exc: Exception | None = None):
        self._value = value
        self._exc = exc

    def create(self, **_kwargs):
        if self._exc is not None:
            raise self._exc
        return self._value


class _FakeAudio:
    def __init__(self, *, value=None, exc: Exception | None = None):
        self.transcriptions = _FakeAudioTranscriptions(value=value, exc=exc)


class _FakeClient:
    def __init__(self, *, model_value=None, chat_value=None, exc: Exception | None = None):
        self.models = _FakeModels(value=model_value, exc=exc)
        self.chat = _FakeChat(value=chat_value, exc=exc)
        self.audio = _FakeAudio(value=None, exc=exc)


class OpenAIClientFallbackTests(unittest.TestCase):
    def test_retries_models_without_proxy_when_proxy_disconnects(self):
        primary = _FakeClient(exc=_remote_protocol_exception())
        direct = _FakeClient(model_value={"status": "ok"})

        with patch.dict(os.environ, {"HTTPS_PROXY": "http://127.0.0.1:7899"}, clear=False):
            with patch("app.services.openai_client._build_openai_client", side_effect=[primary, direct]):
                client = create_openai_client(api_key="test", base_url="https://example.com/v1", timeout=10.0)
                result = client.models.list()

        self.assertEqual({"status": "ok"}, result)

    def test_retries_chat_without_proxy_when_proxy_disconnects(self):
        primary = _FakeClient(exc=_remote_protocol_exception())
        direct = _FakeClient(chat_value={"message": "ok"})

        with patch.dict(os.environ, {"HTTPS_PROXY": "http://127.0.0.1:7899"}, clear=False):
            with patch("app.services.openai_client._build_openai_client", side_effect=[primary, direct]):
                client = create_openai_client(api_key="test", base_url="https://example.com/v1", timeout=10.0)
                result = client.chat.completions.create(model="demo", messages=[{"role": "user", "content": "ok"}])

        self.assertEqual({"message": "ok"}, result)

    def test_does_not_bypass_proxy_when_no_proxy_env_is_present(self):
        primary = _FakeClient(exc=_remote_protocol_exception())

        with patch.dict(os.environ, {}, clear=True):
            with patch("app.services.openai_client._build_openai_client", side_effect=[primary]):
                client = create_openai_client(api_key="test", base_url="https://example.com/v1", timeout=10.0)
                with self.assertRaises(RuntimeError):
                    client.models.list()


if __name__ == "__main__":
    unittest.main()
