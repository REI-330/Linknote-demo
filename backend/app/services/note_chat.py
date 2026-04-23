from __future__ import annotations

import json
import time

from ..analysis import OpenAICompatibleAnalyzer
from ..config.settings import AppConfig, ModelProviderConfig, resolve_provider_api_key
from ..models.note import NoteRecord
from .note_chat_tools import TOOLS, execute_tool
from .provider_catalog import resolve_analysis_target
from .note_result_export import ensure_note_result_snapshot
from .note_retrieval import build_note_chat_context
from .vector_store import VectorStoreManager


SYSTEM_PROMPT = """你是一个视频笔记问答助手。你拥有以下能力：

1. 系统已自动检索了一些相关内容作为初始参考（见下方）
2. 你可以调用工具主动查询更多信息：
- lookup_transcript: 查询视频原始转录文本（支持按时间、关键词、位置筛选）
- get_video_info: 获取视频元信息（标题、作者、简介、标签等）
- get_note_content: 获取完整笔记内容

--- 初始检索内容 ---
{context}
---

回答要求：
- 如果初始检索内容不足以回答问题，请主动调用工具获取更多信息
- 回答关于视频具体原话、细节时，用 lookup_transcript 查询原文
- 回答关于作者、标题等基本信息时，用 get_video_info 查询
- 请用中文回答，保持简洁准确
"""


def answer_note_question(
    config: AppConfig,
    record: NoteRecord,
    question: str,
    history: list[dict[str, str]] | None = None,
    *,
    provider_id: str | None = None,
    model_name: str | None = None,
) -> tuple[str, list[dict[str, object]]]:
    if not question.strip():
        raise RuntimeError("Question cannot be empty.")
    latest_version = record.versions[-1] if record.versions else None
    if latest_version is None:
        raise RuntimeError("This note does not have an analysis result yet.")

    provider, selected_model = resolve_analysis_target(config, provider_id=provider_id, model_name=model_name)
    api_key = resolve_provider_api_key(provider)
    if not api_key:
        raise RuntimeError("API key is not configured.")

    analyzer = OpenAICompatibleAnalyzer(
        provider,
        api_key,
        config.paths.workspace_dir / "notes" / record.item_id / "checkpoints",
    )
    analyzer.model = selected_model
    context, sources = _build_chat_context(config, record, question)
    messages: list[dict[str, object]] = [{"role": "system", "content": SYSTEM_PROMPT.format(context=context)}]

    for message in (history or [])[-20:]:
        role = str(message.get("role") or "").strip()
        content = str(message.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": question.strip()})
    answer = _chat_with_tools(analyzer, record, messages)
    return answer, sources


def _build_chat_context(
    config: AppConfig,
    record: NoteRecord,
    question: str,
) -> tuple[str, list[dict[str, object]]]:
    try:
        store = VectorStoreManager(config)
        if store.is_available:
            ensure_note_result_snapshot(config, record)
            if not store.is_indexed(record.item_id):
                store.index_task(record.item_id)
            chunks = store.query(record.item_id, question, n_results=6)
            if chunks:
                return build_note_chat_context(record, question, chunks)
    except Exception:
        pass
    return build_note_chat_context(record, question)


def _chat_with_tools(analyzer: OpenAICompatibleAnalyzer, record: NoteRecord, messages: list[dict[str, object]]) -> str:
    max_rounds = 3
    tool_mode_failed = False

    for _round in range(max_rounds):
        try:
            response = _chat_completion_create(analyzer, messages, tools=TOOLS)
        except Exception as exc:
            if _tools_are_unsupported(exc):
                tool_mode_failed = True
                break
            raise

        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None) or []
        if not tool_calls:
            return str(message.content or "").strip()

        messages.append(_assistant_tool_message(message))

        for tool_call in tool_calls:
            function = getattr(tool_call, "function", None)
            tool_name = str(getattr(function, "name", "") or "")
            try:
                arguments = json.loads(getattr(function, "arguments", "") or "{}")
            except json.JSONDecodeError:
                arguments = {}

            result = execute_tool(record, tool_name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": getattr(tool_call, "id", ""),
                    "content": result,
                }
            )

    if tool_mode_failed:
        fallback_messages = [
            {"role": message["role"], "content": message["content"]}
            for message in messages
            if message.get("role") in {"system", "user", "assistant"} and isinstance(message.get("content"), str)
        ]
        return analyzer.chat(fallback_messages).strip()

    response = _chat_completion_create(analyzer, messages)
    return str(response.choices[0].message.content or "").strip()


def _chat_completion_create(
    analyzer: OpenAICompatibleAnalyzer,
    messages: list[dict[str, object]],
    *,
    tools: list[dict[str, object]] | None = None,
):
    last_exc = None
    for attempt in range(analyzer.max_retry_attempts):
        try:
            payload: dict[str, object] = {
                "model": analyzer.model,
                "messages": messages,
                "temperature": 0.7,
            }
            if tools is not None:
                payload["tools"] = tools
            return analyzer.client.chat.completions.create(**payload)
        except Exception as exc:
            last_exc = exc
            if attempt == analyzer.max_retry_attempts - 1 or not analyzer._is_retryable_error(exc):
                raise
            time.sleep(analyzer.retry_base_backoff * (2**attempt))
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Chat completion failed without exception.")


def _assistant_tool_message(message) -> dict[str, object]:
    serialized_calls: list[dict[str, object]] = []
    for tool_call in getattr(message, "tool_calls", None) or []:
        function = getattr(tool_call, "function", None)
        serialized_calls.append(
            {
                "id": getattr(tool_call, "id", ""),
                "type": getattr(tool_call, "type", "function"),
                "function": {
                    "name": getattr(function, "name", ""),
                    "arguments": getattr(function, "arguments", "") or "{}",
                },
            }
        )
    return {
        "role": "assistant",
        "content": str(getattr(message, "content", "") or ""),
        "tool_calls": serialized_calls,
    }


def _tools_are_unsupported(exc: Exception) -> bool:
    text = str(exc).lower()
    return "tool" in text and any(
        token in text
        for token in (
            "unsupported",
            "not support",
            "invalid parameter",
            "unknown parameter",
        )
    )
