import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSettingsStore } from "@/stores/settings-store";

const HOUR_OPTIONS = Array.from({ length: 24 }, (_, i) =>
  String(i).padStart(2, "0")
);
const MINUTE_OPTIONS = Array.from({ length: 60 }, (_, i) =>
  String(i).padStart(2, "0")
);
const QUICK_TIMES = ["09:00", "12:00", "18:00", "21:00", "23:00"];

function normalizeDailyTime(value: string) {
  const match = /^(\d{1,2}):(\d{1,2})$/.exec(value.trim());
  if (!match) return "21:00";
  const hour = Number(match[1]);
  const minute = Number(match[2]);
  if (
    !Number.isInteger(hour) ||
    !Number.isInteger(minute) ||
    hour < 0 ||
    hour > 23 ||
    minute < 0 ||
    minute > 59
  ) {
    return "21:00";
  }
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function buildAccountValue(chatlogRoot: string, accountDir: string) {
  return `${chatlogRoot}||${accountDir}`;
}

export function DownloaderSection() {
  const bootstrap = useSettingsStore((s) => s.bootstrap);
  const draft = useSettingsStore((s) => s.draft);
  const updateDraft = useSettingsStore((s) => s.updateDraft);

  if (!draft || !bootstrap) {
    return (
      <Card className="border-dashed shadow-sm">
        <CardContent className="py-12 text-center text-muted-foreground font-medium">
          加载中...
        </CardContent>
      </Card>
    );
  }

  const currentAccountValue = buildAccountValue(
    draft.wechat_chatlog_root,
    draft.wechat_account_dir
  );
  const knownValues = new Set(
    bootstrap.wechat.accounts.map((a) =>
      buildAccountValue(a.chatlog_root, a.account_dir)
    )
  );
  const selectedTime = normalizeDailyTime(draft.daily_time);
  const [selectedHour, selectedMinute] = selectedTime.split(":");

  const toggles = [
    {
      label: "启用 browser cookies fallback",
      checked: draft.bilibili_use_browser_cookies,
      onChange: (v: boolean) =>
        updateDraft({ bilibili_use_browser_cookies: v }),
    },
    {
      label: "启用微信采集",
      checked: draft.wechat_enabled,
      onChange: (v: boolean) => updateDraft({ wechat_enabled: v }),
    },
    {
      label: "启用剪贴板采集",
      checked: draft.clipboard_enabled,
      onChange: (v: boolean) => updateDraft({ clipboard_enabled: v }),
    },
    {
      label: "定时抓取微信",
      checked: draft.auto_collect_wechat,
      onChange: (v: boolean) => updateDraft({ auto_collect_wechat: v }),
    },
    {
      label: "定时抓取剪贴板",
      checked: draft.clipboard_include_on_schedule,
      onChange: (v: boolean) =>
        updateDraft({ clipboard_include_on_schedule: v }),
    },
    {
      label: "启用自动整理",
      checked: draft.schedule_enabled,
      onChange: (v: boolean) => updateDraft({ schedule_enabled: v }),
    },
  ];

  return (
    <div className="space-y-5">
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">来源采集与定时整理</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-semibold">
              Bilibili cookies 文件
            </label>
            <Input
              value={draft.bilibili_cookies_file}
              placeholder="cookies.txt 路径"
              onChange={(e) =>
                updateDraft({ bilibili_cookies_file: e.target.value })
              }
              className="h-10"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="space-y-2">
              <label className="text-sm font-semibold">微信账号</label>
              <Select
                value={currentAccountValue}
                onValueChange={(value) => {
                  const [chatlogRoot, accountDir] = value.split("||");
                  updateDraft({
                    wechat_chatlog_root: chatlogRoot ?? draft.wechat_chatlog_root,
                    wechat_account_dir: accountDir ?? draft.wechat_account_dir,
                  });
                }}
              >
                <SelectTrigger className="h-10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {!knownValues.has(currentAccountValue) && (
                    <SelectItem value={currentAccountValue}>
                      {draft.wechat_account_dir || "当前配置"}
                    </SelectItem>
                  )}
                  {bootstrap.wechat.accounts.map((account) => (
                    <SelectItem
                      key={buildAccountValue(
                        account.chatlog_root,
                        account.account_dir
                      )}
                      value={buildAccountValue(
                        account.chatlog_root,
                        account.account_dir
                      )}
                    >
                      {account.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold">回看天数</label>
              <Input
                type="number"
                min={1}
                value={draft.wechat_scan_days}
                onChange={(e) =>
                  updateDraft({
                    wechat_scan_days: Number(e.target.value) || 3,
                  })
                }
                className="h-10"
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-semibold">
                每日自动整理时间
              </label>
              <div className="flex items-center gap-2">
                <Select
                  value={selectedHour}
                  onValueChange={(h) =>
                    updateDraft({ daily_time: `${h}:${selectedMinute}` })
                  }
                >
                  <SelectTrigger className="w-24 h-10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {HOUR_OPTIONS.map((h) => (
                      <SelectItem key={h} value={h}>
                        {h} 时
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <span className="text-lg font-bold text-muted-foreground">
                  :
                </span>
                <Select
                  value={selectedMinute}
                  onValueChange={(m) =>
                    updateDraft({ daily_time: `${selectedHour}:${m}` })
                  }
                >
                  <SelectTrigger className="w-24 h-10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {MINUTE_OPTIONS.map((m) => (
                      <SelectItem key={m} value={m}>
                        {m} 分
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {QUICK_TIMES.map((time) => (
                  <button
                    key={time}
                    type="button"
                    className={`px-3 py-1.5 rounded-md text-xs border transition-colors font-medium ${
                      selectedTime === time
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-muted text-muted-foreground border-border hover:bg-accent"
                    }`}
                    onClick={() => updateDraft({ daily_time: time })}
                  >
                    {time}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {toggles.map((t) => (
              <label
                key={t.label}
                className="flex items-center justify-between p-3.5 rounded-lg border bg-card/50 hover:bg-accent/40 transition-colors"
              >
                <span className="text-sm font-semibold">{t.label}</span>
                <Switch checked={t.checked} onCheckedChange={t.onChange} />
              </label>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
