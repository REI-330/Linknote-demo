from __future__ import annotations

import json
import re
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:  # pragma: no cover - optional dependency
    chromadb = None
    Settings = None

from ..config.settings import AppConfig
from .note_result_export import note_result_path


def _chunk_markdown(markdown: str) -> list[dict[str, object]]:
    sections = re.split(r"(?=^#{2,3}\s)", markdown, flags=re.MULTILINE)
    chunks: list[dict[str, object]] = []
    for section in sections:
        section = section.strip()
        if not section or len(section) < 30:
            continue
        heading_match = re.match(r"^(#{2,3})\s+(.+)", section)
        title = heading_match.group(2).strip() if heading_match else "intro"
        chunks.append(
            {
                "text": section,
                "metadata": {"source_type": "markdown", "section_title": title},
            }
        )
    return chunks


def _chunk_transcript(
    segments: list[dict[str, object]],
    window_size: int = 15,
    overlap: int = 3,
) -> list[dict[str, object]]:
    if not segments:
        return []
    chunks: list[dict[str, object]] = []
    step = max(window_size - overlap, 1)
    for index in range(0, len(segments), step):
        window = segments[index : index + window_size]
        if not window:
            break
        text = "\n".join(f"[{seg.get('start', 0):.0f}s] {seg.get('text', '')}" for seg in window)
        chunks.append(
            {
                "text": text,
                "metadata": {
                    "source_type": "transcript",
                    "start_time": window[0].get("start", 0),
                    "end_time": window[-1].get("end", 0),
                },
            }
        )
    return chunks


def _build_meta_chunk(audio_meta: dict[str, object]) -> list[dict[str, object]]:
    if not audio_meta:
        return []

    raw = audio_meta.get("raw_info", {}) or {}
    parts: list[str] = []

    title = audio_meta.get("title") or raw.get("title", "")
    if title:
        parts.append(f"视频标题：{title}")

    uploader = raw.get("uploader", "")
    if uploader:
        parts.append(f"视频作者/UP主：{uploader}")

    desc = raw.get("description", "")
    if desc:
        parts.append(f"视频简介：{str(desc)[:500]}")

    tags = raw.get("tags", [])
    if tags and isinstance(tags, list):
        parts.append(f"标签：{', '.join(str(tag) for tag in tags[:20])}")

    duration = audio_meta.get("duration", 0)
    if duration:
        total_seconds = int(float(duration))
        minutes, seconds = divmod(total_seconds, 60)
        parts.append(f"视频时长：{minutes}分{seconds}秒")

    platform = audio_meta.get("platform", "")
    if platform:
        parts.append(f"平台：{platform}")

    url = raw.get("webpage_url", "")
    if url:
        parts.append(f"链接：{url}")

    if not parts:
        return []

    return [{"text": "\n".join(parts), "metadata": {"source_type": "meta"}}]


class VectorStoreManager:
    def __init__(self, config: AppConfig):
        self._config = config
        self._vector_db_dir = _resolve_vector_db_dir(config)
        self._client = None
        if chromadb is not None and Settings is not None:
            self._client = chromadb.PersistentClient(
                path=str(self._vector_db_dir),
                settings=Settings(anonymized_telemetry=False),
            )

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def _collection_name(self, task_id: str) -> str:
        return task_id

    def _note_result_path(self, task_id: str) -> Path:
        return note_result_path(self._config, task_id)

    def index_task(self, task_id: str) -> None:
        if self._client is None:
            raise RuntimeError("chromadb is not installed.")

        result_path = self._note_result_path(task_id)
        if not result_path.exists():
            return

        with result_path.open("r", encoding="utf-8") as handle:
            note_data = json.load(handle)

        markdown = str(note_data.get("markdown", "") or "")
        transcript = note_data.get("transcript", {}) or {}
        segments = transcript.get("segments", []) or []
        audio_meta = note_data.get("audio_meta", {}) or {}

        meta_chunks = _build_meta_chunk(audio_meta)
        md_chunks = _chunk_markdown(markdown)
        tr_chunks = _chunk_transcript(segments)
        all_chunks = meta_chunks + md_chunks + tr_chunks
        if not all_chunks:
            return

        col_name = self._collection_name(task_id)
        try:
            self._client.delete_collection(col_name)
        except Exception:
            pass

        collection = self._client.create_collection(
            name=col_name,
            metadata={"hnsw:space": "cosine"},
        )
        collection.add(
            documents=[chunk["text"] for chunk in all_chunks],
            metadatas=[chunk["metadata"] for chunk in all_chunks],
            ids=[f"{task_id}_{index}" for index in range(len(all_chunks))],
        )

    def _parse_results(self, results: dict[str, object]) -> list[dict[str, object]]:
        chunks: list[dict[str, object]] = []
        documents = results.get("documents") if results else None
        if not documents or not documents[0]:
            return chunks
        metadatas = results.get("metadatas") or []
        distances = results.get("distances") or []
        for index in range(len(documents[0])):
            chunks.append(
                {
                    "text": documents[0][index],
                    "metadata": metadatas[0][index] if metadatas else {},
                    "distance": distances[0][index] if distances else None,
                }
            )
        return chunks

    def query(self, task_id: str, query_text: str, n_results: int = 6) -> list[dict[str, object]]:
        if self._client is None:
            return []

        col_name = self._collection_name(task_id)
        try:
            collection = self._client.get_collection(col_name)
        except Exception:
            return []

        all_chunks: list[dict[str, object]] = []
        quotas = _query_quotas(n_results)
        for source_type, quota in quotas.items():
            try:
                results = collection.query(
                    query_texts=[query_text],
                    n_results=quota,
                    where={"source_type": source_type},
                )
                all_chunks.extend(self._parse_results(results))
            except Exception:
                continue
        return all_chunks

    def delete_index(self, task_id: str) -> None:
        if self._client is None:
            return
        try:
            self._client.delete_collection(self._collection_name(task_id))
        except Exception:
            return

    def is_indexed(self, task_id: str) -> bool:
        if self._client is None:
            return False
        try:
            collection = self._client.get_collection(self._collection_name(task_id))
            if collection.count() == 0:
                return False
            meta = collection.get(where={"source_type": "meta"}, limit=1)
            return len(meta["ids"]) > 0
        except Exception:
            return False


def _query_quotas(n_results: int) -> dict[str, int]:
    if n_results <= 1:
        return {"meta": 1}
    if n_results == 2:
        return {"meta": 1, "markdown": 1}
    if n_results <= 4:
        return {"meta": 1, "markdown": 1, "transcript": max(1, n_results - 2)}
    return {"meta": 1, "markdown": 2, "transcript": max(1, n_results - 3)}


def _resolve_vector_db_dir(config: AppConfig) -> Path:
    candidates = [
        config.paths.runtime_dir,
        config.project_root / "backend" / ".tmp-tests",
        config.project_root / "backend",
    ]
    for candidate in candidates:
        if _is_python_writable_dir(candidate):
            return candidate
    return config.project_root / "backend"


def _is_python_writable_dir(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    probe = path / ".vector-store-write-probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False
