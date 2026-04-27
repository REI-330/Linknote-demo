import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useSettingsStore } from "@/stores/settings-store";

function formatTimestamp(value?: string) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getHealthFollowup(check: {
  key: string;
  status: string;
  detail: string;
  followup?: string;
}) {
  if (check.followup?.trim()) return check.followup.trim();
  if (check.key === "api_key" && check.status !== "ok") {
    return "到设置页填写当前提供商的 API Key，保存后再重试。";
  }
  if (check.key === "bilibili_cookies") {
    if (check.detail.includes("public videos only")) {
      return "公开视频可以直接分析；受限视频请提供 cookies.txt 或启用 browser cookies fallback。";
    }
    if (check.status !== "ok") {
      return "当前 cookies 文件不可用，请检查路径，或改用 browser cookies fallback。";
    }
  }
  if (check.key === "wechat_root" && check.status !== "ok") {
    return "先确认 chatlog 路径存在，再回来读取微信链接。";
  }
  return "";
}

export function MonitorSection() {
  const health = useSettingsStore((s) => s.health);
  const dailyStatus = useSettingsStore((s) => s.dailyStatus);

  const checks = health?.checks ?? [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold">健康检查</CardTitle>
            <Badge
              variant={health?.status === "ok" ? "success" : "warning"}
              className="text-xs font-medium"
            >
              {health?.status ?? "-"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-2.5">
          {checks.map((check) => (
            <div
              key={check.key}
              className={`p-3.5 rounded-lg border space-y-1.5 ${
                check.status === "ok"
                  ? "bg-emerald-50/50 border-emerald-200 dark:bg-emerald-950/20 dark:border-emerald-900"
                  : "bg-amber-50/50 border-amber-200 dark:bg-amber-950/20 dark:border-amber-900"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">{check.label}</span>
                <Badge
                  variant={
                    check.status === "ok" ? "success" : "warning"
                  }
                  className="text-xs font-medium"
                >
                  {check.status}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground font-medium leading-relaxed">
                {check.detail}
              </p>
              {getHealthFollowup(check) && (
                <p className="text-xs text-primary font-medium leading-relaxed">{getHealthFollowup(check)}</p>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold">最近运行</CardTitle>
            <Badge variant="secondary" className="text-xs font-medium">
              {dailyStatus?.last_run?.report_date ?? "-"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-2.5 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground font-medium">定时整理</span>
            <span className="font-medium">{dailyStatus?.schedule_enabled ? "已启用" : "未启用"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground font-medium">每日时间</span>
            <span className="font-medium">{dailyStatus?.daily_time ?? "-"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground font-medium">下次计划</span>
            <span className="font-medium">{formatTimestamp(dailyStatus?.next_run_at)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground font-medium">当前状态</span>
            <span className="font-medium">
              {dailyStatus?.is_running
                ? `运行中${dailyStatus.current_reason ? ` (${dailyStatus.current_reason})` : ""}`
                : "空闲"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground font-medium">完成条目</span>
            <span className="font-medium">{dailyStatus?.last_run?.completed_items ?? 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground font-medium">失败条目</span>
            <span className="font-medium">{dailyStatus?.last_run?.failed_items ?? 0}</span>
          </div>
          {dailyStatus?.last_error && (
            <div className="flex justify-between">
              <span className="text-muted-foreground font-medium">上次错误</span>
              <span className="text-destructive text-xs max-w-[200px] text-right font-medium">
                {dailyStatus.last_error}
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
