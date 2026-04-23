import { Maximize2, Minimize2, Trash2 } from "lucide-react";
import { FormEvent, useState } from "react";

import type { NoteChatSource } from "../types";
import { MarkdownArticle } from "./MarkdownArticle";

type ChatMessage = {
  role: "assistant" | "user";
  content: string;
  sources?: NoteChatSource[];
};

interface NoteChatPanelProps {
  messages: ChatMessage[];
  value: string;
  disabled: boolean;
  loading: boolean;
  blockReason: string | null;
  mode?: "half" | "full";
  onModeChange?: (mode: "half" | "full") => void;
  onClear?: () => void;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}

function formatChatTime(seconds?: number) {
  const safeSeconds = Math.max(0, Math.floor(seconds ?? 0));
  const minutes = Math.floor(safeSeconds / 60);
  const remainSeconds = safeSeconds % 60;
  const hours = Math.floor(minutes / 60);
  const remainMinutes = minutes % 60;
  if (hours > 0) {
    return `${hours}:${String(remainMinutes).padStart(2, "0")}:${String(remainSeconds).padStart(2, "0")}`;
  }
  return `${String(remainMinutes).padStart(2, "0")}:${String(remainSeconds).padStart(2, "0")}`;
}

function buildSourcePreview(text: string) {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (normalized.length <= 220) {
    return normalized;
  }
  return `${normalized.slice(0, 220)}...`;
}

interface SourceCardProps {
  source: NoteChatSource;
  sourceKey: string;
  expanded: boolean;
  onToggle: (sourceKey: string) => void;
}

function SourceCard({ source, sourceKey, expanded, onToggle }: SourceCardProps) {
  const canExpand = source.text.trim().length > 220;
  const showMarkdown = source.source_type === "markdown" && (expanded || !canExpand);

  return (
    <div className="note-chat-source">
      <div className="note-chat-source-head">
        <strong>{source.title ?? "来源片段"}</strong>
        {source.source_type === "transcript" ? (
          <span className="note-chat-source-time">
            {formatChatTime(source.start_time)} - {formatChatTime(source.end_time)}
          </span>
        ) : null}
      </div>
      {showMarkdown ? (
        <div className="note-chat-source-markdown">
          <MarkdownArticle markdown={source.text} />
        </div>
      ) : (
        <p>{expanded ? source.text : buildSourcePreview(source.text)}</p>
      )}
      <div className="note-chat-source-actions">
        {canExpand ? (
          <button type="button" className="link-button" onClick={() => onToggle(sourceKey)}>
            {expanded ? "收起全文" : "展开全文"}
          </button>
        ) : null}
        {source.jump_url ? (
          <a className="link-button" href={source.jump_url} target="_blank" rel="noreferrer">
            {source.source_type === "transcript" ? "跳到原片" : "打开来源"}
          </a>
        ) : null}
      </div>
    </div>
  );
}

export function NoteChatPanel({
  messages,
  value,
  disabled,
  loading,
  blockReason,
  mode = "half",
  onModeChange,
  onClear,
  onChange,
  onSubmit
}: NoteChatPanelProps) {
  const [expandedSources, setExpandedSources] = useState<string[]>([]);

  function toggleSource(sourceKey: string) {
    setExpandedSources((current) =>
      current.includes(sourceKey) ? current.filter((item) => item !== sourceKey) : [...current, sourceKey]
    );
  }

  return (
    <div className="note-chat-panel">
      <div className="note-chat-head">
        <div className="note-chat-head-title">
          <strong>AI 问答</strong>
          <span>基于当前笔记继续追问</span>
        </div>
        <div className="note-chat-head-actions">
          {onModeChange ? (
            <button
              className="bn-ghost-button"
              type="button"
              onClick={() => onModeChange(mode === "half" ? "full" : "half")}
              title={mode === "half" ? "切到全屏" : "切到半屏"}
            >
              {mode === "half" ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
            </button>
          ) : null}
          {onClear && messages.length > 1 ? (
            <button
              className="bn-ghost-button"
              type="button"
              onClick={() => {
                setExpandedSources([]);
                onClear();
              }}
              title="清空问答"
            >
              <Trash2 size={16} />
            </button>
          ) : null}
        </div>
      </div>
      <div className="note-chat-thread">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`note-chat-bubble ${message.role}`}>
            {message.role === "assistant" ? <MarkdownArticle markdown={message.content} /> : message.content}
            {message.role === "assistant" && message.sources?.length ? (
              <div className="note-chat-sources">
                {message.sources.map((source, sourceIndex) => {
                  const sourceKey = `${index}-${sourceIndex}`;
                  return (
                    <SourceCard
                      key={`${source.source_type}-${sourceIndex}`}
                      source={source}
                      sourceKey={sourceKey}
                      expanded={expandedSources.includes(sourceKey)}
                      onToggle={toggleSource}
                    />
                  );
                })}
              </div>
            ) : null}
          </div>
        ))}
      </div>
      <form className="note-chat-form" onSubmit={onSubmit}>
        {blockReason ? <p className="guard-copy chat-guard-copy">{blockReason}</p> : null}
        <div className="note-chat-input-row">
          <input
            placeholder="针对这条笔记继续追问..."
            value={value}
            onChange={(event) => onChange(event.target.value)}
            disabled={disabled}
          />
          <button disabled={disabled}>{loading ? "回答中..." : "发送"}</button>
        </div>
      </form>
    </div>
  );
}
