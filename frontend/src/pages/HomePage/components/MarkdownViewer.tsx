import { Suspense, lazy } from "react";
import type { FormEvent } from "react";

import { MarkdownArticle } from "../../../app/MarkdownArticle";
import { NoteChatPanel } from "../../../app/NoteChatPanel";
import { TranscriptPanel } from "../../../app/TranscriptPanel";
import { VideoBanner } from "../../../app/VideoBanner";
import type { NoteDetail, ReportItem } from "../../../types";
import { MarkdownHeader } from "./MarkdownHeader";
import StepBar from "./StepBar";

type WorkspaceMode = "markdown" | "mindmap";
export type ChatPanelMode = false | "half" | "full";

type ChatMessage = {
  role: "assistant" | "user";
  content: string;
  sources?: Array<{
    text: string;
    source_type: string;
    title?: string;
    section_title?: string;
    start_time?: number;
    end_time?: number;
    jump_url?: string;
  }>;
};

type VersionRecord = NoteDetail["analysis"]["versions"][number] | null;

const MarkmapView = lazy(() => import("../../../app/MarkmapView").then((module) => ({ default: module.MarkmapView })));

const analysisSteps = [
  { label: "读取记录", key: "loading" },
  { label: "整理素材", key: "preparing" },
  { label: "生成笔记", key: "running" },
  { label: "完成保存", key: "success" }
];

export interface MarkdownViewerProps {
  selectedItem: ReportItem | null;
  loadingDetail: boolean;
  detail: NoteDetail | null;
  selectedVersionId: string;
  onSelectVersion: (value: string) => void;
  previewVersion: VersionRecord;
  workspaceMode: WorkspaceMode;
  onToggleWorkspaceMode: () => void;
  copiedMarkdown: boolean;
  onCopyMarkdown: () => void;
  onExportMarkdown: () => void;
  showSourceReference: boolean;
  onToggleSourceReference: () => void;
  chatPanelMode: ChatPanelMode;
  onToggleChatPanel: () => void;
  onChangeChatPanelMode: (mode: ChatPanelMode) => void;
  aiChatEnabled: boolean;
  formatTimestamp: (value?: string) => string;
  formatDuration: (seconds: number) => string;
  workspaceTitle: string;
  selectedProviderSummary: string;
  selectedStyleLabel: string;
  busyAction: string;
  selectedTargetAiBlockReason: string | null;
  onSubmitPrimaryAction: () => void;
  onOpenSettings: () => void;
  chatMessages: ChatMessage[];
  chatQuestion: string;
  onChatQuestionChange: (value: string) => void;
  chatBlockReason: string | null;
  onAskQuestion: (event: FormEvent<HTMLFormElement>) => void;
  onClearChat: () => void;
}

function StageFallback({ title, description, step }: { title: string; description: string; step: string }) {
  return (
    <div className="ln-preview-state">
      <div className="ln-preview-stage-card">
        <StepBar steps={analysisSteps} currentStep={step} />
        <div className="ln-preview-stage-copy">
          <strong>{title}</strong>
          <p>{description}</p>
        </div>
      </div>
    </div>
  );
}

export default function MarkdownViewer({
  selectedItem,
  loadingDetail,
  detail,
  selectedVersionId,
  onSelectVersion,
  previewVersion,
  workspaceMode,
  onToggleWorkspaceMode,
  copiedMarkdown,
  onCopyMarkdown,
  onExportMarkdown,
  showSourceReference,
  onToggleSourceReference,
  chatPanelMode,
  onToggleChatPanel,
  onChangeChatPanelMode,
  aiChatEnabled,
  formatTimestamp,
  formatDuration,
  workspaceTitle,
  selectedProviderSummary,
  selectedStyleLabel,
  busyAction,
  selectedTargetAiBlockReason,
  onSubmitPrimaryAction,
  onOpenSettings,
  chatMessages,
  chatQuestion,
  onChatQuestionChange,
  chatBlockReason,
  onAskQuestion,
  onClearChat
}: MarkdownViewerProps) {
  if (!selectedItem) {
    return (
      <div className="ln-preview-state">
        <div className="ln-preview-empty">
          <strong>输入视频链接，或从历史里选择一条笔记</strong>
          <p>单条工作台会按 LinkNote 的结构展示预览、原文参照和 AI 问答。</p>
        </div>
      </div>
    );
  }

  if (loadingDetail) {
    return <StageFallback title="正在读取这条笔记" description="正在加载分析结果、原文片段和视频信息。" step="preparing" />;
  }

  if (!detail) {
    return (
      <div className="ln-preview-state">
        <div className="ln-preview-empty">
          <strong>这条笔记暂时不可用</strong>
          <p>请重新选择历史记录，或刷新当前日报。</p>
        </div>
      </div>
    );
  }

  const isMindmapMode = workspaceMode === "mindmap";
  const isHalfChatMode = chatPanelMode === "half";
  const isFullChatMode = chatPanelMode === "full";
  const isPending = detail.analysis.status === "pending" && !detail.analysis.versions.length;
  const isRunning = detail.analysis.status === "running" && !detail.analysis.versions.length;
  const showTranscriptPane = showSourceReference && !isMindmapMode && !isFullChatMode;
  const showHalfChatPane = isHalfChatMode && !isMindmapMode;
  const columnClassName = [
    "ln-preview-columns",
    showTranscriptPane ? "with-source" : "",
    showHalfChatPane ? "with-chat" : "",
    showTranscriptPane && showHalfChatPane ? "with-both" : ""
  ]
    .filter(Boolean)
    .join(" ");

  if (isPending) {
    return <StageFallback title="正在生成这条笔记" description="当前条目已进入分析链路，结果会在这里自动刷新。" step="running" />;
  }

  if (isRunning) {
    const progress = detail.analysis.progress;
    const description = progress.detail || detail.analysis.message || "当前条目正在分析中，结果会在这里自动刷新。";
    const timing = [progress.started_at ? `开始：${progress.started_at}` : "", progress.updated_at ? `更新：${progress.updated_at}` : ""]
      .filter(Boolean)
      .join("，");

    return (
      <StageFallback
        title={progress.stage === "transcribing_audio" ? "正在转写长视频音频" : "正在生成这条笔记"}
        description={timing ? `${description}（${timing}）` : description}
        step={progress.step || "running"}
      />
    );
  }

  return (
    <div className="ln-preview-shell">
      <MarkdownHeader
        versions={detail.analysis.versions}
        selectedVersionId={selectedVersionId}
        onSelectVersion={onSelectVersion}
        modelName={previewVersion?.model_name}
        providerSummary={selectedProviderSummary}
        styleLabel={selectedStyleLabel}
        createdAt={previewVersion?.created_at}
        copied={copiedMarkdown}
        onCopy={onCopyMarkdown}
        onDownload={onExportMarkdown}
        showSourceReference={showSourceReference}
        onToggleSourceReference={onToggleSourceReference}
        chatPanelMode={chatPanelMode}
        onToggleChatPanel={onToggleChatPanel}
        aiChatEnabled={aiChatEnabled}
        workspaceMode={workspaceMode}
        onToggleWorkspaceMode={onToggleWorkspaceMode}
        formatTimestamp={formatTimestamp}
      />

      <div className="ln-preview-scroll">
        {isFullChatMode ? (
          <section className="ln-preview-surface ln-preview-standalone">
            <NoteChatPanel
              messages={chatMessages}
              value={chatQuestion}
              disabled={!detail.analysis.versions.length || busyAction === "chat" || Boolean(chatBlockReason)}
              loading={busyAction === "chat"}
              blockReason={chatBlockReason}
              mode="full"
              onModeChange={(mode) => onChangeChatPanelMode(mode)}
              onClear={onClearChat}
              onChange={onChatQuestionChange}
              onSubmit={onAskQuestion}
            />
          </section>
        ) : isMindmapMode ? (
          <section className="ln-preview-surface ln-preview-surface-main ln-preview-standalone">
            {previewVersion ? (
              <Suspense fallback={<div className="ln-preview-empty">正在加载思维导图...</div>}>
                <MarkmapView markdown={previewVersion.markdown} />
              </Suspense>
            ) : (
              <div className="ln-preview-empty">这条笔记还没有生成结果。</div>
            )}
          </section>
        ) : (
          <div className="ln-preview-stack">
            <VideoBanner
              title={workspaceTitle}
              uploader={detail.media.uploader}
              platform={detail.media.platform}
              coverUrl={detail.media.cover_url}
              videoUrl={selectedItem.source_url}
            />

            {detail.analysis.status === "failed" ? (
              <section className="bn-analysis-failure">
                <div className="bn-analysis-failure-head">
                  <div>
                    <strong>本次分析失败</strong>
                    {detail.analysis.failure.title ? <p>{detail.analysis.failure.title}</p> : null}
                  </div>
                  <button className="bn-secondary-button" type="button" disabled={busyAction !== "" || Boolean(selectedTargetAiBlockReason)} onClick={onSubmitPrimaryAction}>
                    {busyAction === "reanalyze" ? "重试中..." : "立即重试"}
                  </button>
                </div>
                {detail.analysis.failure.hint ? <p className="bn-muted-copy">{detail.analysis.failure.hint}</p> : null}
                {detail.analysis.message ? (
                  <details className="bn-failure-raw">
                    <summary>查看原始错误</summary>
                    <pre>{detail.analysis.message}</pre>
                  </details>
                ) : null}
                <div className="bn-mini-actions">
                  <button className="bn-ghost-button" type="button" onClick={onOpenSettings}>
                    打开设置
                  </button>
                  <button
                    className="bn-ghost-button"
                    type="button"
                    disabled={!selectedItem.source_url}
                    onClick={() => window.open(selectedItem.source_url, "_blank", "noopener,noreferrer")}
                  >
                    打开原片
                  </button>
                </div>
              </section>
            ) : null}

            {!detail.analysis.versions.length && selectedTargetAiBlockReason ? <p className="guard-copy">{selectedTargetAiBlockReason}</p> : null}

            <div className={columnClassName}>
              <section className="ln-preview-surface ln-preview-surface-main">
                {previewVersion ? (
                  <MarkdownArticle markdown={previewVersion.markdown} />
                ) : (
                  <div className="ln-preview-empty">
                    <strong>这条笔记还没有生成结果</strong>
                    <p>如果当前 provider 或模型未配置完整，可以先去设置页补齐后再重试。</p>
                  </div>
                )}
              </section>

              {showTranscriptPane ? (
                <aside className="ln-preview-surface ln-preview-surface-side">
                  <TranscriptPanel segments={detail.analysis.source_reference} sourceUrl={selectedItem.source_url} />
                </aside>
              ) : null}

              {showHalfChatPane ? (
                <aside className="ln-preview-surface ln-preview-surface-side">
                  <NoteChatPanel
                    messages={chatMessages}
                    value={chatQuestion}
                    disabled={!detail.analysis.versions.length || busyAction === "chat" || Boolean(chatBlockReason)}
                    loading={busyAction === "chat"}
                    blockReason={chatBlockReason}
                    mode="half"
                    onModeChange={(mode) => onChangeChatPanelMode(mode)}
                    onClear={onClearChat}
                    onChange={onChatQuestionChange}
                    onSubmit={onAskQuestion}
                  />
                </aside>
              ) : null}
            </div>

            {detail.media.duration ? <div className="ln-preview-meta-line">总时长 {formatDuration(detail.media.duration)}</div> : null}
          </div>
        )}
      </div>
    </div>
  );
}
