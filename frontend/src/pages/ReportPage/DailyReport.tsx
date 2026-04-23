import { ArrowUpRight, CalendarDays, Clipboard, LayoutList, MessageSquareShare, RefreshCcw, Settings2 } from "lucide-react";

import type { DailyRunStatus, ReportSummary } from "../../types";

type DailyReportPageProps = {
  report: ReportSummary | null;
  loadingReport: boolean;
  busyAction: string;
  statusLabel: Record<string, string>;
  manualUrl: string;
  onManualUrlChange: (value: string) => void;
  onSubmitManual: () => void;
  onOpenSettings: () => void;
  onOpenItem: (itemId: string) => void;
  onDeleteFailedItem: (itemId: string) => void;
  onRunWechat: () => void;
  onRunWechatFullScan: () => void;
  onRunClipboard: () => void;
  onRunDaily: () => void;
  dailyRunBlockReason: string | null;
  wechatBlockReason: string | null;
  clipboardBlockReason: string | null;
  dailyStatus: DailyRunStatus | null;
  wechatScanDays: number;
  formatTimestamp: (value?: string) => string;
};

function statusTone(status: string) {
  if (status === "completed") {
    return "success";
  }
  if (status === "failed") {
    return "warn";
  }
  return "neutral";
}

function sourceOriginsLabel(origins: string[] | undefined) {
  if (!Array.isArray(origins) || !origins.length) {
    return "-";
  }
  return origins.join(" / ");
}

export function DailyReportPage({
  report,
  loadingReport,
  busyAction,
  statusLabel,
  manualUrl,
  onManualUrlChange,
  onSubmitManual,
  onOpenSettings,
  onOpenItem,
  onDeleteFailedItem,
  onRunWechat,
  onRunWechatFullScan,
  onRunClipboard,
  onRunDaily,
  dailyRunBlockReason,
  wechatBlockReason,
  clipboardBlockReason,
  dailyStatus,
  wechatScanDays,
  formatTimestamp
}: DailyReportPageProps) {
  const items = Array.isArray(report?.items) ? report.items : [];
  const publishTime = dailyStatus?.daily_time || "21:00";
  const scheduleEnabled = Boolean(dailyStatus?.schedule_enabled);
  const nextRunLabel = scheduleEnabled ? formatTimestamp(dailyStatus?.next_run_at) : "未启用";

  return (
    <div className="bn-report-page">
      <header className="bn-report-hero">
        <div className="bn-report-hero-copy">
          <span className="bn-pill neutral">日报入口</span>
          <h1>今日采集列表</h1>
          <p>首页只保留日报卡片流。点开任意条目后，再进入 LinkNote 单条分析工作台。</p>
        </div>
        <div className="bn-report-hero-actions">
          <button className="bn-secondary-button" type="button" onClick={onOpenSettings}>
            <Settings2 size={16} />
            设置
          </button>
        </div>
      </header>

      <section className="bn-report-summary-strip">
        <article className="bn-report-summary-card">
          <span>日报日期</span>
          <strong>{report?.report_date ?? "-"}</strong>
        </article>
        <article className="bn-report-summary-card">
          <span>总条目</span>
          <strong>{report?.total_items ?? 0}</strong>
        </article>
        <article className="bn-report-summary-card">
          <span>已完成</span>
          <strong>{report?.completed_items ?? 0}</strong>
        </article>
        <article className="bn-report-summary-card">
          <span>失败 / 排队</span>
          <strong>
            {(report?.failed_items ?? 0)} / {(report?.pending_items ?? 0)}
          </strong>
        </article>
      </section>

      <section className="bn-report-actions-panel">
        <div className="bn-report-manual-box">
          <div className="bn-report-manual-head">
            <strong>手动补充链接</strong>
            <span>粘贴 B 站链接后直接加入日报</span>
          </div>
          <div className="bn-report-manual-row">
            <input
              value={manualUrl}
              placeholder="https://www.bilibili.com/video/..."
              onChange={(event) => onManualUrlChange(event.target.value)}
            />
            <button className="bn-primary-button" type="button" disabled={busyAction !== "" || !manualUrl.trim()} onClick={onSubmitManual}>
              {busyAction === "manual" ? "加入中..." : "加入日报"}
            </button>
          </div>
        </div>

        <div className="bn-report-quick-actions">
          <button className="bn-secondary-button" type="button" disabled={busyAction !== "" || Boolean(wechatBlockReason)} onClick={onRunWechat}>
            <MessageSquareShare size={16} />
            {busyAction === "wechat" ? "读取中..." : "读取微信"}
          </button>
          <button className="bn-secondary-button" type="button" disabled={busyAction !== "" || Boolean(wechatBlockReason)} onClick={onRunWechatFullScan}>
            <RefreshCcw size={16} />
            {busyAction === "wechat-full" ? "补扫中..." : "补扫旧链接"}
          </button>
          <button className="bn-secondary-button" type="button" disabled={busyAction !== "" || Boolean(clipboardBlockReason)} onClick={onRunClipboard}>
            <Clipboard size={16} />
            {busyAction === "clipboard" ? "读取中..." : "读取剪贴板"}
          </button>
          <button className="bn-secondary-button" type="button" disabled={busyAction !== "" || Boolean(dailyRunBlockReason)} onClick={onRunDaily}>
            <CalendarDays size={16} />
            {busyAction === "daily-run" ? "整理中..." : "立即整理"}
          </button>
        </div>

        <div className="bn-report-status-stack">
          <div className="bn-report-timing-box">
            <div className="bn-report-timing-head">
              <strong>自动整理窗口</strong>
              <span>{scheduleEnabled ? `每日 ${publishTime}` : "当前关闭"}</span>
            </div>
            <div className="bn-report-guide-list">
              <p>{scheduleEnabled ? `今天的自动整理会在 ${publishTime} 触发。` : "自动整理当前未启用，只会在你手动读取或立即整理时更新日报。"}</p>
              <p>微信默认只回看最近 {wechatScanDays} 天；更早的链接需要点“补扫旧链接”重新回扫。</p>
              <p>如果今天新链接还没出现在日报里，通常要么还没到自动整理时间，要么还没有手动点“立即整理”。</p>
            </div>
            <div className="bn-report-timing-meta">
              <span>下一次自动整理</span>
              <strong>{nextRunLabel}</strong>
            </div>
          </div>

          {dailyStatus?.last_run ? (
            <div className="bn-report-last-run">
              <span>最近一次整理</span>
              <strong>{dailyStatus.last_run.report_date}</strong>
              <p>
                完成 {dailyStatus.last_run.completed_items} 条，失败 {dailyStatus.last_run.failed_items} 条
              </p>
            </div>
          ) : null}
        </div>
      </section>

      <section className="bn-report-list">
        <div className="bn-report-list-head">
          <div>
            <strong>日报条目</strong>
            <p>{loadingReport ? "正在刷新列表..." : `共 ${items.length} 条，可逐条进入单条分析页。`}</p>
          </div>
          <span className="bn-pill neutral">
            <LayoutList size={14} />
            卡片流
          </span>
        </div>

        {items.length ? (
          <div className="bn-report-card-list">
            {items.map((item) => (
              <article key={item.item_id} className="bn-report-card">
                <div className="bn-report-card-top">
                  <span className={`bn-pill ${statusTone(item.status)}`}>{statusLabel[item.status] ?? item.status}</span>
                  <span className="bn-report-card-time">{item.collected_at || "--"}</span>
                </div>

                <div className="bn-report-card-body">
                  <strong>{item.source_title}</strong>
                  <p>{item.status === "failed" && item.failure_title ? item.failure_title : item.source_context}</p>
                </div>

                <div className="bn-report-card-meta">
                  <span>来源：{sourceOriginsLabel(item.source_origins)}</span>
                  <span>版本：{item.versions}</span>
                </div>

                <div className="bn-report-card-actions">
                  <button className="bn-primary-button" type="button" onClick={() => onOpenItem(item.item_id)}>
                    进入单条页
                    <ArrowUpRight size={15} />
                  </button>
                  {item.status === "failed" ? (
                    <button
                      className="bn-ghost-button warn"
                      type="button"
                      disabled={busyAction !== ""}
                      onClick={() => onDeleteFailedItem(item.item_id)}
                    >
                      {busyAction === `delete-failed:${item.item_id}` ? "删除中..." : "删除记录"}
                    </button>
                  ) : null}
                  <button
                    className="bn-ghost-button"
                    type="button"
                    onClick={() => window.open(item.source_url, "_blank", "noopener,noreferrer")}
                  >
                    打开原片
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="bn-empty-box">
            <div>
              <strong>今天还没有日报条目</strong>
              <p>先读取微信、剪贴板，或手动补一条 B 站链接。</p>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
