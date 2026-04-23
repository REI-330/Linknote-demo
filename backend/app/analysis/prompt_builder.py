from __future__ import annotations

from .prompt_templates import BASE_PROMPT


NOTE_FORMATS = [
    {"label": "目录", "value": "toc"},
    {"label": "原片跳转", "value": "link"},
    {"label": "原片截图", "value": "screenshot"},
    {"label": "AI总结", "value": "summary"},
]


NOTE_STYLES = [
    {"label": "精简", "value": "minimal"},
    {"label": "详细", "value": "detailed"},
    {"label": "学术", "value": "academic"},
    {"label": "教程", "value": "tutorial"},
    {"label": "小红书", "value": "xiaohongshu"},
    {"label": "生活向", "value": "life_journal"},
    {"label": "任务导向", "value": "task_oriented"},
    {"label": "商业风格", "value": "business"},
    {"label": "会议纪要", "value": "meeting_minutes"},
]


def generate_base_prompt(
    title: str,
    segment_text: str,
    tags: str | list[str],
    *,
    format_values: list[str] | None = None,
    style_value: str | None = None,
    extras: str | None = None,
) -> str:
    tags_text = ", ".join(tags) if isinstance(tags, list) else str(tags or "")
    prompt = BASE_PROMPT.format(
        video_title=title,
        segment_text=segment_text,
        tags=tags_text,
    )

    if format_values:
        instructions = [_format_instruction(value) for value in format_values]
        prompt += "\n" + "\n".join(item for item in instructions if item)
    if style_value:
        style_instruction = _style_instruction(style_value)
        if style_instruction:
            prompt += "\n" + style_instruction
    if extras:
        prompt += f"\n{extras.strip()}"
    return prompt.strip()


def _format_instruction(format_value: str) -> str:
    mapping = {
        "toc": (
            "9. 目录：自动生成基于 `##` 和 `###` 标题的清晰目录结构。"
        ),
        "link": (
            "10. 原片跳转：为每个主要章节标题追加时间戳标记，格式必须是 "
            "`*Content-[mm:ss]`，并且放在标题后面。"
        ),
        "screenshot": (
            "11. 原片截图：如果某一节涉及 UI 操作、代码演示、视觉对比或明显依赖画面理解的内容，"
            "在该节末尾插入 `*Screenshot-[mm:ss]` 标记，只在确实有帮助时使用。"
        ),
        "summary": (
            "12. AI总结：在笔记末尾追加二级标题 `## AI 总结`，用简洁中文概括整条内容。"
        ),
    }
    return mapping.get(format_value, "")


def _style_instruction(style_value: str) -> str:
    mapping = {
        "minimal": "风格要求：尽量精简，只保留最关键的信息。",
        "detailed": "风格要求：尽量详细，完整记录上下文、推导和细节。",
        "academic": "风格要求：偏学术表达，结构严谨，术语准确。",
        "tutorial": "风格要求：偏教程式整理，突出步骤、方法、注意事项和可复现操作。",
        "xiaohongshu": (
            "风格要求：模仿小红书式表达，标题和段落更有传播性，但仍要忠实原文，"
            "不要为了夸张而编造内容。"
        ),
        "life_journal": "风格要求：偏生活记录和个人感受整理，语气自然，但仍保留信息密度。",
        "task_oriented": "风格要求：偏任务导向，突出行动项、步骤、落地建议和执行顺序。",
        "business": "风格要求：偏商业汇报，表达正式，结论优先，突出收益、问题和决策点。",
        "meeting_minutes": "风格要求：偏会议纪要，突出议题、观点、结论、分工和后续动作。",
    }
    return mapping.get(style_value, "")
