export type TranscriptSegment = {
  start: number;
  end: number;
  text: string;
  speaker: string;
};

interface TranscriptPanelProps {
  segments: TranscriptSegment[] | undefined;
  sourceUrl: string;
}

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function buildSourceJumpUrl(baseUrl: string, seconds: number) {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  return baseUrl.includes("?") ? `${baseUrl}&t=${safeSeconds}` : `${baseUrl}?t=${safeSeconds}`;
}

export function TranscriptPanel({ segments, sourceUrl }: TranscriptPanelProps) {
  const safeSegments = Array.isArray(segments) ? segments : [];

  if (!safeSegments.length) {
    return <div className="flex min-h-[220px] items-center justify-center px-6 text-sm text-muted-foreground">暂无片段</div>;
  }

  return (
    <div className="flex h-full flex-col bg-transparent">
      <div className="grid grid-cols-[72px_1fr] gap-3 border-b border-border/45 px-5 py-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        <span>时间</span>
        <span>原文片段</span>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="space-y-3 px-4 py-4">
          {safeSegments.map((segment, index) => (
            <article
              key={`${segment.start}-${index}`}
              className="rounded-[1rem] border border-border/45 bg-card/74 px-4 py-4 shadow-[0_12px_38px_-32px_rgba(22,59,114,0.42)]"
            >
              <div className="grid grid-cols-[72px_1fr] gap-3">
                <a
                  href={buildSourceJumpUrl(sourceUrl, segment.start)}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-semibold text-primary hover:underline"
                >
                  {formatTime(segment.start)}
                </a>
                <div>
                  {segment.speaker ? (
                    <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                      {segment.speaker}
                    </div>
                  ) : null}
                  <p className="text-[15px] leading-8 text-foreground/90 xl:text-base">{segment.text}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-border/45 px-5 py-3 text-xs font-semibold text-muted-foreground">
        <span>{safeSegments.length} 条</span>
        <span>{formatTime(safeSegments[safeSegments.length - 1]?.end || 0)}</span>
      </div>
    </div>
  );
}
