from __future__ import annotations

from ..analysis.prompt_builder import generate_base_prompt
from ..config.settings import AppConfig
from ..models.note import NoteRecord


def build_preview_markdown(config: AppConfig, record: NoteRecord) -> str:
    prompt_preview = generate_base_prompt(
        record.source_title or record.source_url,
        record.source_context,
        record.metadata.get("tags", []) if isinstance(record.metadata.get("tags"), list) else [],
        format_values=[config.analysis.note_format, "link"] if config.analysis.enable_source_links else [config.analysis.note_format],
        style_value=config.analysis.note_style,
        extras="当前仅用于迁移期版本链路联调，不代表最终分析质量。",
    )
    return "\n".join(
        [
            f"# {record.source_title or 'LinkNote 笔记'}",
            "",
            "> 迁移预览版本",
            "",
            f"- 来源链接：{record.source_url}",
            f"- 来源类型：{' + '.join(record.source_origins) if record.source_origins else 'unknown'}",
            f"- 当前状态：分析链路正在迁移，真实 BiliNote 级分析尚未接入。",
            "",
            "## 当前捕获内容",
            "",
            record.source_context or "暂无原始上下文。",
            "",
            "## 迁移说明",
            "",
            "- 这个版本仅用于打通单条详情页、多版本堆叠、导出和后续问答接线。",
            "- 下一步会替换成 B 站字幕/转写驱动的真实分析内容。",
            "",
            "## Prompt Preview",
            "",
            "```text",
            prompt_preview,
            "```",
        ]
    ).strip()

