type TranscriptSegment = {
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
    return (
      <div className="transcript-panel-empty">
        <p>这里会优先展示平台字幕，没有字幕时展示转写文本。</p>
        <p>你可以在 AI 笔记和原文之间直接对照，不需要跳到别的页面。</p>
      </div>
    );
  }

  return (
    <div className="transcript-panel">
      <div className="transcript-panel-head">
        <span>时间</span>
        <span>内容</span>
      </div>
      <div className="transcript-panel-body">
        {safeSegments.map((segment, index) => (
          <article key={`${segment.start}-${index}`} className="transcript-row">
            <a className="transcript-time" href={buildSourceJumpUrl(sourceUrl, segment.start)} target="_blank" rel="noreferrer">
              {formatTime(segment.start)}
            </a>
            <div className="transcript-copy">
              {segment.speaker ? <span className="transcript-speaker">{segment.speaker}</span> : null}
              <p>{segment.text}</p>
            </div>
          </article>
        ))}
      </div>
      <div className="transcript-panel-foot">
        <span>共 {safeSegments.length} 条片段</span>
        <span>总时长: {formatTime(safeSegments[safeSegments.length - 1]?.end || 0)}</span>
      </div>
    </div>
  );
}
