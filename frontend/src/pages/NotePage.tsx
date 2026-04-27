import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  BookOpen,
  BrainCircuit,
  Copy,
  Download,
  GitBranchPlus,
  RotateCcw,
  Settings2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useNoteStore } from "@/stores/note-store";
import { useReportStore } from "@/stores/report-store";
import { useSettingsStore } from "@/stores/settings-store";
import { useUiStore } from "@/stores/ui-store";
import { MarkdownArticle } from "@/app/MarkdownArticle";
import { MarkmapView } from "@/app/MarkmapView";
import { TranscriptPanel } from "@/app/TranscriptPanel";

function formatDuration(seconds: number) {
  const safe = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(safe / 60);
  const remainSeconds = safe % 60;
  const hours = Math.floor(minutes / 60);
  const remainMinutes = minutes % 60;

  if (hours > 0) {
    return `${hours}:${String(remainMinutes).padStart(2, "0")}:${String(remainSeconds).padStart(2, "0")}`;
  }

  return `${remainMinutes}:${String(remainSeconds).padStart(2, "0")}`;
}

function sanitizeFilename(input: string) {
  return input.replace(/[<>:"/\\|?*\u0000-\u001F]/g, "").trim() || "linknote-export";
}

function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 30000);
}

function buildProgressRows(stage: string) {
  const lower = stage.toLowerCase();

  if (lower.includes("summar") || lower.includes("generat") || lower.includes("analy")) {
    return [
      { label: "文本解析", value: 100 },
      { label: "知识结构", value: 72 },
      { label: "摘要生成", value: 45 },
    ];
  }

  if (lower.includes("transcrib") || lower.includes("download") || lower.includes("audio")) {
    return [
      { label: "文本解析", value: 32 },
      { label: "知识结构", value: 0 },
      { label: "摘要生成", value: 0 },
    ];
  }

  return [
    { label: "文本解析", value: 12 },
    { label: "知识结构", value: 0 },
    { label: "摘要生成", value: 0 },
  ];
}

function LoadingWorkspace({
  title,
  sourceUrl,
  detail,
  stage,
}: {
  title: string;
  sourceUrl?: string;
  detail: string;
  stage: string;
}) {
  const progressRows = buildProgressRows(stage);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-5 py-6 md:px-10 md:py-8">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-5 text-slate-200/88">
        <div className="flex items-center gap-3">
          <Link to="/" className="ln-icon-button border-white/10 bg-white/5 text-slate-100 hover:bg-white/10">
            <ArrowLeft className="h-4.5 w-4.5" />
          </Link>
          <div>
            <h1 className="max-w-2xl truncate text-xl font-semibold tracking-tight text-slate-50">{title}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs font-medium text-slate-400">
              <span className="ln-pill border-white/10 bg-white/5 text-slate-300">Generating</span>
              {sourceUrl ? <span className="truncate">{sourceUrl}</span> : null}
            </div>
          </div>
        </div>
        <Link
          to="/settings/model"
          className="ln-action-button border-white/10 bg-white/5 text-slate-100 hover:bg-white/10"
        >
          <Settings2 className="h-4 w-4" />
          模型设置
        </Link>
      </div>

      <div className="grid flex-1 gap-6 py-6 lg:grid-cols-12">
        <div className="relative overflow-hidden rounded-[1.5rem] border border-white/10 bg-[radial-gradient(circle_at_center,_rgba(152,203,255,0.08),_transparent_54%),linear-gradient(180deg,rgba(7,12,21,0.96),rgba(10,17,31,1))] px-6 py-10 lg:col-span-8">
          <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_top,_rgba(139,185,255,0.12),_transparent_36%)]" />
          <div className="relative z-10 flex h-full flex-col">
            <div className="mb-8 flex items-center gap-3">
              <span className="rounded-full border border-sky-200/20 bg-sky-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-sky-200">
                Knowledge Weaving
              </span>
            </div>

            <div className="flex flex-1 flex-col items-center justify-center">
              <div className="relative mb-10 h-64 w-64">
                <svg className="absolute inset-0 h-full w-full text-sky-200/20" viewBox="0 0 100 100" aria-hidden="true">
                  <path
                    d="M50 50 L20 30 M50 50 L80 20 M50 50 L30 80 M50 50 L85 65 M20 30 L40 10 M80 20 L90 45"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="0.35"
                  />
                  <circle cx="20" cy="30" r="1" fill="currentColor" />
                  <circle cx="80" cy="20" r="1.5" fill="currentColor" />
                  <circle cx="30" cy="80" r="0.85" fill="currentColor" />
                  <circle cx="85" cy="65" r="1.2" fill="currentColor" />
                  <circle cx="40" cy="10" r="0.55" fill="currentColor" />
                  <circle cx="90" cy="45" r="0.75" fill="currentColor" />
                </svg>
                <div className="absolute inset-1/2 flex h-16 w-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-sky-200/20 bg-sky-300/10 shadow-[0_0_45px_rgba(139,185,255,0.18)] backdrop-blur-xl">
                  <BrainCircuit className="h-7 w-7 text-sky-200" />
                </div>
              </div>

              <h2 className="text-center text-2xl font-semibold tracking-[0.06em] text-sky-100">正在生成分析</h2>
              <p className="mt-4 max-w-xl text-center text-sm leading-7 text-slate-400 md:text-base">{detail}</p>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-5 lg:col-span-4">
          <div className="rounded-[1.4rem] border border-white/10 bg-slate-950/70 p-6 text-slate-100 shadow-[0_28px_70px_-42px_rgba(0,0,0,0.8)]">
            <h3 className="mb-4 text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">分析进度</h3>
            <div className="space-y-4">
              {progressRows.map((row) => (
                <div key={row.label}>
                  <div className="mb-1 flex items-center justify-between text-xs font-semibold text-slate-400">
                    <span>{row.label}</span>
                    <span>{row.value === 0 ? "等待中" : `${row.value}%`}</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-white/8">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${row.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function NotePage() {
  const { itemId } = useParams<{ itemId: string }>();
  const report = useReportStore((state) => state.report);
  const reportDate = report?.report_date;

  const detail = useNoteStore((state) => state.detail);
  const loading = useNoteStore((state) => state.loading);
  const busyAction = useNoteStore((state) => state.busyAction);
  const selectedVersionId = useNoteStore((state) => state.selectedVersionId);
  const showSourceReference = useNoteStore((state) => state.showSourceReference);
  const refreshNote = useNoteStore((state) => state.refreshNote);
  const reanalyze = useNoteStore((state) => state.reanalyze);
  const setSelectedVersionId = useNoteStore((state) => state.setSelectedVersionId);
  const toggleSourceReference = useNoteStore((state) => state.toggleSourceReference);
  const resetNote = useNoteStore((state) => state.resetNote);

  const settingsDraft = useSettingsStore((state) => state.draft);
  const health = useSettingsStore((state) => state.health);
  const desktopSidebarCollapsed = useUiStore((state) => state.desktopSidebarCollapsed);

  const [showMindMap, setShowMindMap] = useState(false);
  const [hideCoverImage, setHideCoverImage] = useState(false);
  const [showDesktopToolbar, setShowDesktopToolbar] = useState(false);
  const [mindmapSvgMarkup, setMindmapSvgMarkup] = useState<string | null>(null);

  useEffect(() => {
    if (itemId) {
      refreshNote(itemId, reportDate);
    }

    return () => {
      resetNote();
    };
  }, [itemId, reportDate, refreshNote, resetNote]);

  useEffect(() => {
    setHideCoverImage(false);
  }, [detail?.media.cover_url, itemId]);

  const selectedItem = useMemo(
    () => report?.items.find((item) => item.item_id === itemId),
    [itemId, report]
  );

  const aiBlockReason = useMemo(() => {
    if (!settingsDraft) return null;
    if (!settingsDraft.analysis_provider_id || !settingsDraft.analysis_model_name) {
      return "当前还没有配置分析模型。";
    }
    if (health?.checks.find((check) => check.key === "provider_auth")?.status !== "ok") {
      return "当前分析模型鉴权不可用。";
    }
    return null;
  }, [health, settingsDraft]);

  useEffect(() => {
    if (
      !detail ||
      !selectedItem ||
      busyAction !== "" ||
      selectedItem.status !== "pending" ||
      detail.analysis.status !== "pending" ||
      detail.analysis.versions.length > 0 ||
      aiBlockReason
    ) {
      return;
    }

    reanalyze(detail.item.item_id, reportDate);
  }, [aiBlockReason, busyAction, detail, reanalyze, reportDate, selectedItem]);

  const previewVersion = useMemo(
    () =>
      detail?.analysis.versions.find((version) => version.version_id === selectedVersionId) ??
      detail?.analysis.versions[0] ??
      null,
    [detail, selectedVersionId]
  );

  const activeProviderSummary = previewVersion?.provider_id
    ? `${previewVersion.provider_id} / ${previewVersion.model_name || ""}`
    : "未生成";

  const showGeneratingScreen =
    loading ||
    !detail ||
    (detail.analysis.status === "running" && detail.analysis.versions.length === 0) ||
    (detail.analysis.status === "pending" &&
      detail.analysis.versions.length === 0 &&
      busyAction !== "" &&
      !aiBlockReason);

  const showPendingEmptyState =
    detail &&
    detail.analysis.status === "pending" &&
    detail.analysis.versions.length === 0 &&
    !showGeneratingScreen;

  const exportBaseName = useMemo(
    () => sanitizeFilename(detail?.item.source_title || selectedItem?.source_title || "linknote-analysis"),
    [detail?.item.source_title, selectedItem?.source_title]
  );

  function handleExportAnalysis() {
    if (!previewVersion) {
      return;
    }

    if (showMindMap) {
      if (!mindmapSvgMarkup) {
        window.alert("思维导图尚未准备完成，请稍后再试。");
        return;
      }

      downloadBlob(
        `${exportBaseName}-思维导图.svg`,
        new Blob([mindmapSvgMarkup], { type: "image/svg+xml;charset=utf-8" })
      );
      return;
    }

    downloadBlob(
      `${exportBaseName}.md`,
      new Blob([previewVersion.markdown], { type: "text/markdown;charset=utf-8" })
    );
  }

  function handleExportTranscript() {
    const content = (detail.analysis.source_reference || [])
      .map((segment) => (segment.speaker ? `${segment.speaker}: ${segment.text}` : segment.text))
      .join("\n\n")
      .trim();

    if (!content) {
      return;
    }

    downloadBlob(`${exportBaseName}-原文转写.txt`, new Blob([content], { type: "text/plain;charset=utf-8" }));
  }

  function renderToolbarButtons() {
    const exportDisabled = showMindMap ? !mindmapSvgMarkup : !previewVersion;

    return (
      <>
        <button
          type="button"
          className="ln-floating-button"
          disabled={busyAction !== "" || Boolean(aiBlockReason)}
          onClick={() => itemId && reanalyze(itemId, reportDate)}
        >
          <RotateCcw className="h-4 w-4" />
          {busyAction === "reanalyze" ? "重试中..." : "重新分析"}
        </button>
        <div className="h-5 w-px bg-border/70" />
        <button
          type="button"
          className="ln-floating-button"
          onClick={() => {
            if (previewVersion) {
              navigator.clipboard.writeText(previewVersion.markdown).catch(() => undefined);
            }
          }}
        >
          <Copy className="h-4 w-4" />
          复制 Markdown
        </button>
        <button
          type="button"
          className={cn("ln-floating-button", showMindMap && "ln-floating-button-active")}
          onClick={() => setShowMindMap((value) => !value)}
        >
          <GitBranchPlus className="h-4 w-4" />
          思维导图
        </button>
        <button
          type="button"
          className={cn("ln-floating-button", showSourceReference && "ln-floating-button-active")}
          onClick={toggleSourceReference}
        >
          <BookOpen className="h-4 w-4" />
          原文片段
        </button>
        <button
          type="button"
          className="ln-floating-button"
          disabled={exportDisabled}
          onClick={handleExportAnalysis}
        >
          <Download className="h-4 w-4" />
          导出
        </button>
      </>
    );
  }

  if (showGeneratingScreen) {
    return (
      <LoadingWorkspace
        title={detail?.item.source_title || selectedItem?.source_title || "正在准备当前笔记"}
        sourceUrl={detail?.item.source_url || selectedItem?.source_url}
        detail={detail?.analysis.progress.detail || "分析进行中"}
        stage={detail?.analysis.progress.stage || detail?.analysis.status || "pending"}
      />
    );
  }

  if (!detail) {
    return null;
  }

  return (
    <div
      className={cn(
        "mx-auto flex w-full flex-1 flex-col px-5 py-6 md:px-10 md:py-8",
        desktopSidebarCollapsed ? "max-w-[1540px]" : "max-w-[1320px]"
      )}
    >
      <header className="mb-5 flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="ln-tag">{detail.media.platform || "内容条目"}</span>
          <span className="ln-tag">{activeProviderSummary}</span>
          {detail.media.duration ? <span className="ln-tag">{formatDuration(detail.media.duration)}</span> : null}
          {detail.media.uploader ? <span className="ln-tag">{detail.media.uploader}</span> : null}
        </div>

        {detail.analysis.status === "failed" ? (
          <div className="ln-panel flex flex-col gap-3 border-destructive/20 bg-destructive/5 px-5 py-4 text-sm text-destructive md:flex-row md:items-start md:justify-between">
            <div>
              <strong className="font-semibold">本次分析失败</strong>
              {detail.analysis.failure.title ? <p className="mt-1">{detail.analysis.failure.title}</p> : null}
              {detail.analysis.failure.hint ? (
                <p className="mt-1 text-destructive/80">{detail.analysis.failure.hint}</p>
              ) : null}
            </div>
            <button
              type="button"
              className="ln-action-button text-destructive hover:text-destructive"
              disabled={busyAction !== "" || Boolean(aiBlockReason)}
              onClick={() => itemId && reanalyze(itemId, reportDate)}
            >
              <RotateCcw className="h-4 w-4" />
              {busyAction === "reanalyze" ? "重试中..." : "立即重试"}
            </button>
          </div>
        ) : null}

        {showPendingEmptyState ? (
          <div className="ln-panel border-amber-500/20 bg-amber-500/5 px-5 py-4 text-sm text-amber-700 dark:text-amber-200">
            <strong className="font-semibold">当前还没有开始分析</strong>
            <p className="mt-1">{aiBlockReason || detail.analysis.message || "暂无结果"}</p>
          </div>
        ) : null}
      </header>

      <div
        className={cn(
          "grid flex-1 items-start gap-6",
          showSourceReference
            ? desktopSidebarCollapsed
              ? "xl:grid-cols-[minmax(0,1.16fr)_minmax(28rem,1fr)] 2xl:grid-cols-[minmax(0,1.1fr)_minmax(32rem,1fr)]"
              : "xl:grid-cols-[minmax(0,1.12fr)_minmax(25rem,0.9fr)] 2xl:grid-cols-[minmax(0,1.08fr)_minmax(30rem,0.95fr)]"
            : "grid-cols-1"
        )}
      >
        <section className="ln-panel relative overflow-hidden">
          {detail.media.cover_url && !hideCoverImage ? (
            <div className="relative h-52 overflow-hidden border-b border-border/45">
              <img
                src={detail.media.cover_url}
                alt={detail.item.source_title}
                className="h-full w-full object-cover"
                onError={() => setHideCoverImage(true)}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-card via-card/38 to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 flex flex-wrap items-center gap-2 px-6 pb-5">
                <span className="ln-tag bg-white/78 text-primary">AI 生成结果</span>
                <span className="ln-tag bg-white/68">{showMindMap ? "思维导图" : "Markdown 正文"}</span>
              </div>
            </div>
          ) : null}

          <div className="border-b border-border/45 px-6 py-5">
            <div className="flex flex-wrap items-center gap-2">
              {detail.analysis.versions.map((version) => (
                <button
                  key={version.version_id}
                  type="button"
                  className={cn(
                    "rounded-full px-3 py-1.5 text-xs font-semibold transition-colors",
                    previewVersion?.version_id === version.version_id
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary/70 text-muted-foreground hover:bg-accent hover:text-foreground"
                  )}
                  onClick={() => setSelectedVersionId(version.version_id)}
                >
                  {version.label || version.version_id.slice(0, 8)}
                </button>
              ))}
            </div>
          </div>

          <div className="p-6 md:p-7">
            {previewVersion ? (
              showMindMap ? (
                <MarkmapView
                  markdown={previewVersion.markdown}
                  exportFilename={`${exportBaseName}-思维导图.svg`}
                  onExportSvgChange={setMindmapSvgMarkup}
                />
              ) : (
                <MarkdownArticle
                  markdown={previewVersion.markdown}
                  className={cn(!showSourceReference && "markdown-article-expanded")}
                />
              )
            ) : (
              <div className="py-10 text-sm text-muted-foreground">暂无结果</div>
            )}
          </div>
        </section>

        {showSourceReference ? (
          <aside className="flex flex-col gap-6 self-start xl:sticky xl:top-6">
            <div className="ln-panel px-6 py-6 xl:flex xl:h-[calc(100dvh-7.5rem)] xl:flex-col">
              <div className="mb-4 flex items-center justify-between gap-3">
                <h3 className="text-lg font-semibold text-foreground">原文片段</h3>
                <button type="button" className="ln-action-button px-3 py-2 text-xs" onClick={handleExportTranscript}>
                  <Download className="h-4 w-4" />
                  导出转写
                </button>
              </div>
              <div className="overflow-hidden rounded-[1rem] border border-border/45 xl:min-h-0 xl:flex-1">
                <TranscriptPanel segments={detail.analysis.source_reference} sourceUrl={detail.item.source_url} />
              </div>
            </div>
          </aside>
        ) : null}
      </div>

      <div className="ln-floating-toolbar bottom-24 md:hidden">{renderToolbarButtons()}</div>

      <div
        className="fixed inset-x-0 bottom-0 z-30 hidden h-20 md:block"
        onMouseEnter={() => setShowDesktopToolbar(true)}
      />

      <div
        className={cn(
          "fixed left-1/2 z-40 hidden -translate-x-1/2 transition-all duration-300 ease-out md:block",
          showDesktopToolbar ? "bottom-5 opacity-100" : "pointer-events-none bottom-[-5rem] opacity-0"
        )}
        onMouseEnter={() => setShowDesktopToolbar(true)}
        onMouseLeave={() => setShowDesktopToolbar(false)}
      >
        <div className="ln-floating-toolbar static bottom-auto left-auto translate-x-0">{renderToolbarButtons()}</div>
      </div>
    </div>
  );
}
