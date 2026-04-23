import { SettingsSectionFrame, ToggleField } from "../../app/FormPieces";
import type { SettingsBootstrap, SettingsUpdatePayload } from "../../types";

const DEFAULT_DAILY_TIME = "21:00";
const HOUR_OPTIONS = Array.from({ length: 24 }, (_, index) => String(index).padStart(2, "0"));
const MINUTE_OPTIONS = Array.from({ length: 60 }, (_, index) => String(index).padStart(2, "0"));
const QUICK_DAILY_TIMES = ["09:00", "12:00", "18:00", "21:00", "23:00"];

interface DownloaderPageProps {
  settingsDraft: SettingsUpdatePayload | null;
  wechatAccounts: SettingsBootstrap["wechat"]["accounts"];
  autostartEnabled: boolean;
  onUpdateSettingsDraft: (patch: Partial<SettingsUpdatePayload>) => void;
  saveAction: React.ReactNode;
}

function buildAccountValue(chatlogRoot: string, accountDir: string) {
  return `${chatlogRoot}||${accountDir}`;
}

function normalizeDailyTime(value: string) {
  const match = /^(\d{1,2}):(\d{1,2})$/.exec(value.trim());
  if (!match) {
    return DEFAULT_DAILY_TIME;
  }
  const hour = Number(match[1]);
  const minute = Number(match[2]);
  if (!Number.isInteger(hour) || !Number.isInteger(minute) || hour < 0 || hour > 23 || minute < 0 || minute > 59) {
    return DEFAULT_DAILY_TIME;
  }
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

export default function DownloaderPage({
  settingsDraft,
  wechatAccounts,
  autostartEnabled,
  onUpdateSettingsDraft,
  saveAction,
}: DownloaderPageProps) {
  if (!settingsDraft) {
    return null;
  }

  const currentAccountValue = buildAccountValue(settingsDraft.wechat_chatlog_root, settingsDraft.wechat_account_dir);
  const knownAccountValues = new Set(wechatAccounts.map((item) => buildAccountValue(item.chatlog_root, item.account_dir)));
  const selectedDailyTime = normalizeDailyTime(settingsDraft.daily_time);
  const [selectedHour, selectedMinute] = selectedDailyTime.split(":");

  return (
    <SettingsSectionFrame title="下载配置" subtitle="来源采集、微信账号与自动整理" action={saveAction}>
      <section className="bn-settings-card">
        <div className="bn-settings-form-grid">
          <label className="bn-field wide">
            <span>Bilibili cookies 文件</span>
            <input
              value={settingsDraft.bilibili_cookies_file}
              onChange={(event) => onUpdateSettingsDraft({ bilibili_cookies_file: event.target.value })}
              placeholder="cookies.txt 路径"
            />
          </label>

          <label className="bn-field">
            <span>微信账号</span>
            <select
              value={currentAccountValue}
              onChange={(event) => {
                const [chatlogRoot, accountDir] = event.target.value.split("||");
                onUpdateSettingsDraft({
                  wechat_chatlog_root: chatlogRoot ?? settingsDraft.wechat_chatlog_root,
                  wechat_account_dir: accountDir ?? settingsDraft.wechat_account_dir,
                });
              }}
            >
              {!knownAccountValues.has(currentAccountValue) ? (
                <option value={currentAccountValue}>{settingsDraft.wechat_account_dir || "当前配置"}</option>
              ) : null}
              {wechatAccounts.map((account) => (
                <option key={buildAccountValue(account.chatlog_root, account.account_dir)} value={buildAccountValue(account.chatlog_root, account.account_dir)}>
                  {account.label}
                </option>
              ))}
            </select>
          </label>

          <label className="bn-field">
            <span>微信 chatlog 根目录</span>
            <input
              value={settingsDraft.wechat_chatlog_root}
              onChange={(event) => onUpdateSettingsDraft({ wechat_chatlog_root: event.target.value })}
            />
          </label>

          <label className="bn-field">
            <span>微信账号目录</span>
            <input
              value={settingsDraft.wechat_account_dir}
              onChange={(event) => onUpdateSettingsDraft({ wechat_account_dir: event.target.value })}
            />
          </label>

          <label className="bn-field">
            <span>回看天数</span>
            <input
              type="number"
              min={1}
              value={settingsDraft.wechat_scan_days}
              onChange={(event) => onUpdateSettingsDraft({ wechat_scan_days: Number(event.target.value) || 3 })}
            />
          </label>

          <label className="bn-field">
            <span>每日自动整理时间</span>
            <div className="bn-time-picker" role="group" aria-label="每日自动整理时间">
              <div className="bn-time-picker-row">
                <select value={selectedHour} onChange={(event) => onUpdateSettingsDraft({ daily_time: `${event.target.value}:${selectedMinute}` })}>
                  {HOUR_OPTIONS.map((hour) => (
                    <option key={hour} value={hour}>
                      {hour} 时
                    </option>
                  ))}
                </select>
                <span className="bn-time-picker-separator">:</span>
                <select value={selectedMinute} onChange={(event) => onUpdateSettingsDraft({ daily_time: `${selectedHour}:${event.target.value}` })}>
                  {MINUTE_OPTIONS.map((minute) => (
                    <option key={minute} value={minute}>
                      {minute} 分
                    </option>
                  ))}
                </select>
              </div>

              <div className="bn-time-quick-list">
                {QUICK_DAILY_TIMES.map((time) => (
                  <button
                    key={time}
                    className={selectedDailyTime === time ? "bn-time-chip active" : "bn-time-chip"}
                    type="button"
                    onClick={() => onUpdateSettingsDraft({ daily_time: time })}
                  >
                    {time}
                  </button>
                ))}
              </div>
            </div>
          </label>
        </div>

        <div className="bn-check-grid">
          <ToggleField
            label="启用 browser cookies fallback"
            checked={settingsDraft.bilibili_use_browser_cookies}
            onChange={(checked) => onUpdateSettingsDraft({ bilibili_use_browser_cookies: checked })}
          />
          <ToggleField label="启用微信采集" checked={settingsDraft.wechat_enabled} onChange={(checked) => onUpdateSettingsDraft({ wechat_enabled: checked })} />
          <ToggleField label="启用剪贴板采集" checked={settingsDraft.clipboard_enabled} onChange={(checked) => onUpdateSettingsDraft({ clipboard_enabled: checked })} />
          <ToggleField label="定时抓取微信" checked={settingsDraft.auto_collect_wechat} onChange={(checked) => onUpdateSettingsDraft({ auto_collect_wechat: checked })} />
          <ToggleField
            label="定时抓取剪贴板"
            checked={settingsDraft.clipboard_include_on_schedule}
            onChange={(checked) => onUpdateSettingsDraft({ clipboard_include_on_schedule: checked })}
          />
          <ToggleField label="启用自动整理" checked={settingsDraft.schedule_enabled} onChange={(checked) => onUpdateSettingsDraft({ schedule_enabled: checked })} />
        </div>

        <div className="bn-monitor-copy">
          <p>当前自动整理{settingsDraft.schedule_enabled ? "已开启" : "未开启"}，保存后会同步{settingsDraft.schedule_enabled ? "配置" : "取消"}开机自启。</p>
          <p>当前开机自启状态：{autostartEnabled ? "已配置" : "未配置"}</p>
          <p>微信默认只回看最近 {settingsDraft.wechat_scan_days} 天；超出这个窗口的历史链接，不会在日常增量读取里自动补回。</p>
          <p>当天新链接通常会在 {selectedDailyTime} 的自动整理后进入日报；如果你想提前看到它们，需要回到首页手动执行“读取微信”或“立即整理”。</p>
          <p>如果要把更早的 `filehelper` 历史重新扫一遍，去首页用“补扫旧链接”，它会忽略上次扫描进度并按当前回看天数重扫。</p>
        </div>
      </section>
    </SettingsSectionFrame>
  );
}
