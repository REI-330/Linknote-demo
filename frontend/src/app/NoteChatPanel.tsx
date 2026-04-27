import { FormEvent, useState } from "react";
import { Maximize2, Minimize2, Send, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { NoteChatSource } from "@/types";
import { MarkdownArticle } from "./MarkdownArticle";

export type ChatMessage = {
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
  const safe = Math.max(0, Math.floor(seconds ?? 0));
  const minutes = Math.floor(safe / 60);
  const remainSeconds = safe % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainSeconds).padStart(2, "0")}`;
}

function buildSourcePreview(text: string) {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (normalized.length <= 180) {
    return normalized;
  }
  return `${normalized.slice(0, 180)}...`;
}

function SourceCard({
  source,
  expanded,
  onToggle,
}: {
  source: NoteChatSource;
  expanded: boolean;
  onToggle: () => void;
}) {
  const canExpand = source.text.trim().length > 180;
  const showMarkdown = source.source_type === "markdown" && (expanded || !canExpand);

  return (
    <div className="rounded-[1rem] border border-border/45 bg-card/70 p-3.5">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <strong className="block truncate text-sm font-semibold text-foreground">
            {source.title ?? source.section_title ?? "来源片段"}
          </strong>
          {source.source_type === "transcript" ? (
            <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              {formatChatTime(source.start_time)} - {formatChatTime(source.end_time)}
            </span>
          ) : null}
        </div>
      </div>
      {showMarkdown ? (
        <MarkdownArticle markdown={source.text} />
      ) : (
        <p className="text-sm leading-7 text-muted-foreground">
          {expanded ? source.text : buildSourcePreview(source.text)}
        </p>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs font-semibold">
        {canExpand ? (
          <button type="button" className="text-primary hover:underline" onClick={onToggle}>
            {expanded ? "收起全文" : "展开全文"}
          </button>
        ) : null}
        {source.jump_url ? (
          <a href={source.jump_url} target="_blank" rel="noreferrer" className="text-primary hover:underline">
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
  onSubmit,
}: NoteChatPanelProps) {
  const [expandedSources, setExpandedSources] = useState<string[]>([]);

  function toggleSource(key: string) {
    setExpandedSources((current) =>
      current.includes(key) ? current.filter((item) => item !== key) : [...current, key]
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between border-b border-border/45 px-5 py-4">
        <div>
          <h3 className="text-base font-semibold text-foreground">AI 追问</h3>
          <p className="text-xs font-medium text-muted-foreground">围绕当前笔记继续提问</p>
        </div>
        <div className="flex items-center gap-1">
          {onModeChange ? (
            <button
              type="button"
              className="ln-icon-button h-9 w-9"
              onClick={() => onModeChange(mode === "half" ? "full" : "half")}
            >
              {mode === "half" ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
            </button>
          ) : null}
          {onClear && messages.length > 1 ? (
            <button
              type="button"
              className="ln-icon-button h-9 w-9"
              onClick={() => {
                setExpandedSources([]);
                onClear();
              }}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          ) : null}
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-4 px-5 py-5">
          {messages.map((message, index) => (
            <article
              key={`${message.role}-${index}`}
              className={cn(
                "rounded-[1.2rem] px-4 py-4",
                message.role === "assistant"
                  ? "border border-border/45 bg-card/72"
                  : "ml-6 bg-primary/10 text-foreground"
              )}
            >
              {message.role === "assistant" ? (
                <MarkdownArticle markdown={message.content} />
              ) : (
                <p className="text-sm font-semibold leading-7">{message.content}</p>
              )}

              {message.role === "assistant" && message.sources?.length ? (
                <div className="mt-4 space-y-3">
                  {message.sources.map((source, sourceIndex) => {
                    const key = `${index}-${sourceIndex}`;
                    return (
                      <SourceCard
                        key={key}
                        source={source}
                        expanded={expandedSources.includes(key)}
                        onToggle={() => toggleSource(key)}
                      />
                    );
                  })}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      </ScrollArea>

      <form onSubmit={onSubmit} className="border-t border-border/45 p-5">
        {blockReason ? (
          <p className="mb-3 text-xs font-semibold text-muted-foreground">{blockReason}</p>
        ) : null}
        <div className="flex gap-2">
          <Input
            value={value}
            onChange={(event) => onChange(event.target.value)}
            disabled={disabled}
            placeholder="针对这条笔记继续追问..."
            className="h-11 rounded-2xl border-border/55 bg-card/72"
          />
          <button
            type="submit"
            disabled={disabled}
            className="ln-action-button ln-action-button-primary h-11 min-w-[92px]"
          >
            <Send className="h-4 w-4" />
            {loading ? "回答中..." : "发送"}
          </button>
        </div>
      </form>
    </div>
  );
}
