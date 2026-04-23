import { SettingsSectionFrame } from "../../app/FormPieces";
import type { DailyRunStatus, HealthBootstrap } from "../../types";

interface MonitorPageProps {
  health: HealthBootstrap | null;
  dailyStatus: DailyRunStatus | null;
  formatTimestamp: (value?: string) => string;
  getHealthFollowup: (check: HealthBootstrap["checks"][number]) => string;
  saveAction?: React.ReactNode;
}

function runningLabel(dailyStatus: DailyRunStatus | null) {
  if (!dailyStatus?.is_running) {
    return "空闲";
  }
  return dailyStatus.current_reason ? `运行中 (${dailyStatus.current_reason})` : "运行中";
}

export default function MonitorPage({ health, dailyStatus, formatTimestamp, getHealthFollowup }: MonitorPageProps) {
  const checks = Array.isArray(health?.checks) ? health.checks : [];

  return (
    <SettingsSectionFrame title="部署监控" subtitle="健康检查与最近运行状态">
      <div className="bn-monitor-grid">
        <section className="bn-settings-card">
          <div className="bn-settings-card-head">
            <h3>健康检查</h3>
            <span className={`bn-pill ${health?.status === "ok" ? "success" : "warn"}`}>{health?.status ?? "-"}</span>
          </div>
          <div className="bn-health-list">
            {checks.map((check) => (
              <article key={check.key} className={`bn-health-card ${check.status === "ok" ? "ok" : "warn"}`}>
                <strong>{check.label}</strong>
                <p>{check.detail}</p>
                {getHealthFollowup(check) ? <span>{getHealthFollowup(check)}</span> : null}
              </article>
            ))}
          </div>
        </section>

        <section className="bn-settings-card">
          <div className="bn-settings-card-head">
            <h3>最近运行</h3>
            <span className="bn-pill neutral">{dailyStatus?.last_run?.report_date ?? "-"}</span>
          </div>
          <div className="bn-monitor-copy">
            <p>定时整理：{dailyStatus?.schedule_enabled ? "已启用" : "未启用"}</p>
            <p>每日时间：{dailyStatus?.daily_time ?? "-"}</p>
            <p>下次计划：{formatTimestamp(dailyStatus?.next_run_at)}</p>
            <p>当前状态：{runningLabel(dailyStatus)}</p>
            <p>开始时间：{formatTimestamp(dailyStatus?.last_started_at)}</p>
            <p>结束时间：{formatTimestamp(dailyStatus?.last_finished_at)}</p>
            <p>触发方式：{dailyStatus?.last_reason ?? "-"}</p>
            <p>完成条目：{dailyStatus?.last_run?.completed_items ?? 0}</p>
            <p>失败条目：{dailyStatus?.last_run?.failed_items ?? 0}</p>
            {dailyStatus?.last_error ? <p>上次错误：{dailyStatus.last_error}</p> : null}
          </div>
        </section>
      </div>
    </SettingsSectionFrame>
  );
}
