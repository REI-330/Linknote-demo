from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True)
class ChunkPayload:
    segments: list
    image_urls: list[str]


class RequestChunker:
    def __init__(self, message_builder: Callable, max_bytes: int, size_estimator: Callable | None = None):
        self.message_builder = message_builder
        self.max_bytes = max_bytes
        self.size_estimator = size_estimator

    def estimate(self, messages: list[dict[str, object]]) -> int:
        if self.size_estimator is not None:
            return int(self.size_estimator(messages))
        import json

        return len(json.dumps(messages, ensure_ascii=False).encode("utf-8"))

    def _messages_size(self, segments: list, image_urls: list[str], **kwargs) -> int:
        return self.estimate(self.message_builder(segments, image_urls, **kwargs))

    def _segment_text(self, segment) -> str:
        return getattr(segment, "text", "") if not isinstance(segment, dict) else str(segment.get("text", ""))

    def _clone_segment(self, segment, text: str):
        if isinstance(segment, dict):
            cloned = dict(segment)
            cloned["text"] = text
            return cloned
        payload = {
            "start": getattr(segment, "start", 0),
            "end": getattr(segment, "end", 0),
            "text": text,
        }
        if hasattr(segment, "speaker"):
            payload["speaker"] = getattr(segment, "speaker", "")
        return type(segment)(**payload)

    def _split_segment_to_fit(self, segment, **kwargs):
        text = self._segment_text(segment)
        if not text:
            raise ValueError("empty segment cannot be split")
        low = 1
        high = len(text)
        best = None
        while low <= high:
            middle = (low + high) // 2
            candidate = self._clone_segment(segment, text[:middle])
            if self._messages_size([candidate], [], **kwargs) <= self.max_bytes:
                best = middle
                low = middle + 1
            else:
                high = middle - 1
        if best is None:
            raise ValueError("single segment exceeds request budget")
        return self._clone_segment(segment, text[:best]), self._clone_segment(segment, text[best:])

    def chunk(self, segments: list, image_urls: list[str], **kwargs) -> list[ChunkPayload]:
        segments = list(segments or [])
        image_urls = list(image_urls or [])
        if not segments and not image_urls:
            return []

        chunks: list[ChunkPayload] = []
        index = 0
        while index < len(segments):
            batch: list = []
            while index < len(segments):
                candidate = batch + [segments[index]]
                if self._messages_size(candidate, [], **kwargs) <= self.max_bytes:
                    batch = candidate
                    index += 1
                    continue
                if not batch:
                    head, tail = self._split_segment_to_fit(segments[index], **kwargs)
                    segments[index] = head
                    segments.insert(index + 1, tail)
                    continue
                break
            chunks.append(ChunkPayload(segments=batch, image_urls=[]))

        if not image_urls:
            return chunks

        if not chunks:
            chunks = [ChunkPayload(segments=[], image_urls=[])]

        for image_url in image_urls:
            placed = False
            for chunk in chunks:
                candidate = chunk.image_urls + [image_url]
                if self._messages_size(chunk.segments, candidate, **kwargs) <= self.max_bytes:
                    chunk.image_urls = candidate
                    placed = True
                    break
            if not placed:
                if self._messages_size([], [image_url], **kwargs) > self.max_bytes:
                    raise ValueError("single image exceeds request budget")
                chunks.append(ChunkPayload(segments=[], image_urls=[image_url]))

        return chunks

    def group_texts_by_budget(self, texts: list[str], build_messages: Callable, **kwargs) -> list[list[str]]:
        groups: list[list[str]] = []
        index = 0
        while index < len(texts):
            group: list[str] = []
            while index < len(texts):
                candidate = group + [texts[index]]
                messages = build_messages(candidate, **kwargs)
                if self.estimate(messages) <= self.max_bytes:
                    group = candidate
                    index += 1
                    continue
                if not group:
                    raise ValueError("single text block exceeds request budget")
                break
            groups.append(group)
        return groups
