import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowUpRight,
  CalendarDays,
  ClipboardPaste,
  Link2,
  MessageSquareShare,
  RefreshCcw,
  Settings2,
  Trash2,
  WandSparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useReportStore } from "@/stores/report-store";
import { useSettingsStore } from "@/stores/settings-store";

const statusMap: Record<
  string,
  { label: string; tone: string; dot: string }
> = {
  pending: { label: "待分析", tone: "text-slate-500", dot: "bg-slate-400" },
  running: { label: "分析中", tone: "text-primary", dot: "bg-primary" },
  completed: { label: "已完成", tone: "text-emerald-600 dark:text-emerald-300", dot: "bg-emerald-500" },
  failed: { label: "失败", tone: "text-rose-600 dark:text-rose-300", dot: "bg-rose-500" },
};

function formatChineseDate(value?: string) {
  if (!value) {
    return "今日工作台";
  }
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  }).format(date);
}

function formatTime(value?: string) {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function getSourceKind(item: { source_url: string; source_origins: string[] }) {
  const primaryOrigin = item.source_origins[0] || "";
  if (primaryOrigin) {
    return primaryOrigin;
  }
  if (item.source_url.includes("bilibili")) {
    return "Bilibili";
  }
  if (item.source_url.includes("mp.weixin.qq.com")) {
    return "公众号";
  }
  return "网页";
}

export function DailyReportPage() {
  const [manualUrl, setManualUrl] = useState("");
  const report = useReportStore((state) => state.report);
  const loading = useReportStore((state) => state.loading);
  const busyAction = useReportStore((state) => state.busyAction);
  const ingestWechat = useReportStore((state) => state.ingestWechat);
  const ingestClipboardAction = useReportStore((state) => state.ingestClipboard);
  const ingestManual = useReportStore((state) => state.ingestManual);
  const runDaily = useReportStore((state) => state.runDaily);
  const deleteFailedItem = useReportStore((state) => state.deleteFailedItem);

  const dailyStatus = useSettingsStore((state) => state.dailyStatus);

  const items = report?.items ?? [];
  const summary = useMemo(
    () => [
      { label: "待分析", value: report?.pending_items ?? 0, dot: "bg-slate-400" },
      { label: "分析中", value: items.filter((item) => item.status === "running").length, dot: "bg-primary" },
      { label: "已完成", value: report?.completed_items ?? 0, dot: "bg-emerald-500" },
      { label: "失败", value: report?.failed_items ?? 0, dot: "bg-rose-500" },
    ],
    [items, report]
  );

  const isBusy = busyAction !== "";

  return (
    <div className="mx-auto flex w-full max-w-[1100px] flex-1 flex-col gap-8 px-5 py-6 md:px-10 md:py-10">
      <header className="flex flex-col gap-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-primary/80">
              Daily Feed
            </div>
            <h1 className="ln-section-title">{formatChineseDate(report?.report_date)}</h1>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground md:text-base">
              今天也是整理链接、提炼观点与生成笔记的一天。
            </p>
          </div>
          <Link
            to="/settings/model"
            className="ln-action-button self-start md:self-auto"
          >
            <Settings2 className="h-4 w-4" />
            模型与设置
          </Link>
        </div>

        <div className="ln-panel-soft inline-flex w-fit flex-wrap items-center gap-4 px-5 py-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CalendarDays className="h-4 w-4 text-primary" />
            <span>
              今日收集 <strong className="font-semibold text-foreground">{report?.total_items ?? 0}</strong> 条
            </span>
          </div>
          <div className="hidden h-4 w-px bg-border md:block" />
          <div className="flex flex-wrap items-center gap-4 text-xs font-semibold text-muted-foreground">
            {summary.map((item) => (
              <span key={item.label} className="inline-flex items-center gap-2">
                <span className={cn("ln-status-dot", item.dot)} />
                {item.label} {item.value}
              </span>
            ))}
          </div>
        </div>
      </header>

      <section className="ln-glass rounded-[1.45rem] p-2.5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="ln-input-shell flex-1">
            <Link2 className="h-4.5 w-4.5 text-primary" />
            <input
              className="ln-input"
              type="text"
              placeholder="粘贴链接，或输入待整理的文本片段..."
              value={manualUrl}
              onChange={(event) => setManualUrl(event.target.value)}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="ln-action-button"
              disabled={isBusy}
              onClick={() => ingestWechat(false)}
            >
              <MessageSquareShare className="h-4 w-4" />
              {busyAction === "wechat" ? "读取中..." : "读取微信"}
            </button>
            <button
              type="button"
              className="ln-action-button"
              disabled={isBusy}
              onClick={() => ingestClipboardAction()}
            >
              <ClipboardPaste className="h-4 w-4" />
              {busyAction === "clipboard" ? "读取中..." : "读取剪贴板"}
            </button>
            <button
              type="button"
              className="ln-action-button ln-action-button-primary disabled:opacity-100 disabled:bg-primary disabled:text-primary-foreground"
              disabled={isBusy || !manualUrl.trim()}
              onClick={() => {
                ingestManual(manualUrl);
                setManualUrl("");
              }}
            >
              <WandSparkles className="h-4 w-4" />
              {busyAction === "manual" ? "整理中..." : "立即整理"}
            </button>
          </div>
        </div>
      </section>

      <section className="flex flex-col gap-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold tracking-tight text-foreground">今日条目</h2>
            <span className="ln-pill">{items.length} 条</span>
            {loading ? (
              <span className="text-xs font-semibold text-primary">列表刷新中</span>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="ln-action-button"
              disabled={isBusy}
              onClick={() => ingestWechat(true)}
            >
              <RefreshCcw className="h-4 w-4" />
              {busyAction === "wechat-full" ? "补扫中..." : "补扫旧链接"}
            </button>
            <button
              type="button"
              className="ln-action-button ln-action-button-primary"
              disabled={isBusy}
              onClick={() => runDaily(dailyStatus?.include_clipboard)}
            >
              <WandSparkles className="h-4 w-4" />
              {busyAction === "daily-run" ? "整理中..." : "运行日报流程"}
            </button>
          </div>
        </div>

        {items.length === 0 ? (
          <div className="ln-panel flex min-h-[320px] items-center justify-center px-6 py-12 text-center">
            <div className="max-w-md">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Link2 className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">今天还没有新的日报条目</h3>
              <p className="mt-2 text-sm leading-7 text-muted-foreground">
                先从微信、剪贴板或手动输入收集一条链接，系统会按设计稿的流程继续整理。
              </p>
            </div>
          </div>
        ) : (
          <div className="pl-3 md:pl-4">
            {items.map((item) => {
              const status = statusMap[item.status] ?? statusMap.pending;
              const description =
                item.status === "failed" && item.failure_title
                  ? item.failure_title
                  : item.source_context || "等待提取更多上下文内容。";

              return (
                <article key={item.item_id} className="ln-list-item border-b border-border/40 px-0 last:border-b-0 md:px-4">
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="mb-3 flex flex-wrap items-center gap-2">
                        <span className="ln-tag">{getSourceKind(item)}</span>
                        <span className="ln-tag">{item.source_url.includes("bilibili") ? "视频" : "文本"}</span>
                        <span className={cn("inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-semibold", status.tone, "bg-card/75")}>
                          <span className={cn("ln-status-dot", status.dot)} />
                          {status.label}
                        </span>
                        <span className="text-xs font-medium text-muted-foreground">
                          {item.collected_at || "--"}
                        </span>
                      </div>
                      <h3 className="truncate text-[1.2rem] font-semibold tracking-tight text-foreground">
                        {item.source_title || "未命名条目"}
                      </h3>
                      <p className="mt-2 max-w-3xl text-sm leading-7 text-muted-foreground">
                        {description}
                      </p>
                    </div>

                    <div className="flex shrink-0 flex-wrap gap-2">
                      <Link to={`/notes/${item.item_id}`} className="ln-action-button ln-action-button-primary">
                        进入工作台
                        <ArrowUpRight className="h-4 w-4" />
                      </Link>
                      <button
                        type="button"
                        className="ln-action-button"
                        onClick={() => window.open(item.source_url, "_blank", "noopener,noreferrer")}
                      >
                        打开原片
                      </button>
                      {item.status === "failed" ? (
                        <button
                          type="button"
                          className="ln-action-button text-rose-600 hover:text-rose-700 dark:text-rose-300"
                          disabled={isBusy}
                          onClick={() => deleteFailedItem(item.item_id)}
                        >
                          <Trash2 className="h-4 w-4" />
                          {busyAction === `delete-failed:${item.item_id}` ? "删除中..." : "删除"}
                        </button>
                      ) : null}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <footer className="mt-auto flex flex-col gap-2 border-t border-border/35 pt-6 text-xs font-semibold text-muted-foreground md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap items-center gap-3">
          <span>下次计划运行: {dailyStatus?.daily_time ?? "--"}</span>
          <span className="h-1 w-1 rounded-full bg-border" />
          <span>最近成功: {formatTime(dailyStatus?.last_finished_at)}</span>
        </div>
        <div className="flex items-center gap-2 text-primary">
          <span className="ln-status-dot bg-primary" />
          <span>{dailyStatus?.is_running ? "流程运行中" : "运行正常"}</span>
        </div>
      </footer>
    </div>
  );
}
