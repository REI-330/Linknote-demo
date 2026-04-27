import { create } from "zustand";
import {
  getDailyStatus,
  getHealthBootstrap,
  getSettingsBootstrap,
  saveSettings,
} from "@/api";
import type {
  DailyRunStatus,
  HealthBootstrap,
  SettingsBootstrap,
  SettingsUpdatePayload,
} from "@/types";

function normalizeDailyTime(value?: string) {
  const match = /^(\d{1,2}):(\d{1,2})$/.exec((value ?? "").trim());
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

function buildDraft(
  bootstrap: SettingsBootstrap | null
): SettingsUpdatePayload | null {
  if (!bootstrap) return null;
  return {
    wechat_enabled: bootstrap.wechat.enabled,
    wechat_chatlog_root: bootstrap.wechat.chatlog_root,
    wechat_account_dir: bootstrap.wechat.account_dir,
    wechat_scan_days: bootstrap.wechat.scan_days,
    clipboard_enabled: bootstrap.clipboard.enabled,
    bilibili_cookies_file: bootstrap.bilibili.cookies_file,
    bilibili_use_browser_cookies: bootstrap.bilibili.use_browser_cookies,
    schedule_enabled: bootstrap.schedule.enabled,
    daily_time: normalizeDailyTime(bootstrap.schedule.daily_time),
    auto_collect_wechat: bootstrap.schedule.auto_collect_wechat,
    notify_on_complete: bootstrap.schedule.notify_on_complete,
    clipboard_include_on_schedule: bootstrap.clipboard.include_on_schedule,
    retention_days: bootstrap.retention.days,
    cleanup_intermediate: bootstrap.retention.cleanup_intermediate,
    note_format: bootstrap.analysis.note_format,
    note_style: bootstrap.analysis.note_style,
    enable_source_links: bootstrap.analysis.enable_source_links,
    enable_mind_map: bootstrap.analysis.enable_mind_map,
    enable_ai_chat: bootstrap.analysis.enable_ai_chat,
    enable_screenshots: bootstrap.analysis.enable_screenshots,
    analysis_provider_id: bootstrap.analysis.provider_id,
    analysis_model_name: bootstrap.analysis.model_name,
    server_host: bootstrap.server.host,
    server_port: bootstrap.server.port,
    server_open_browser: bootstrap.server.open_browser,
    lan_enabled: bootstrap.server.lan_enabled,
    notification_enabled: bootstrap.notification.enabled,
    notification_open_target: bootstrap.notification.open_target,
    transcriber_type: bootstrap.transcriber.type,
    transcriber_provider_id: bootstrap.transcriber.provider_id,
    transcriber_model_name: bootstrap.transcriber.model_name,
    transcriber_language: bootstrap.transcriber.language,
    providers: bootstrap.providers.map((p) => ({ ...p })),
  };
}

interface SettingsState {
  bootstrap: SettingsBootstrap | null;
  draft: SettingsUpdatePayload | null;
  dailyStatus: DailyRunStatus | null;
  health: HealthBootstrap | null;
  loading: boolean;
  busyAction: string;
  error: string | null;

  refreshSettings: () => Promise<void>;
  refreshDailyStatus: () => Promise<void>;
  refreshHealth: () => Promise<void>;
  refreshAll: () => Promise<void>;
  saveAll: () => Promise<void>;
  updateDraft: (patch: Partial<SettingsUpdatePayload>) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  bootstrap: null,
  draft: null,
  dailyStatus: null,
  health: null,
  loading: false,
  busyAction: "",
  error: null,

  refreshSettings: async () => {
    try {
      const bootstrap = await getSettingsBootstrap();
      set({ bootstrap, draft: buildDraft(bootstrap) });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    }
  },

  refreshDailyStatus: async () => {
    try {
      const dailyStatus = await getDailyStatus();
      set({ dailyStatus });
    } catch {
      /* ignore */
    }
  },

  refreshHealth: async () => {
    try {
      const health = await getHealthBootstrap();
      set({ health });
    } catch {
      /* ignore */
    }
  },

  refreshAll: async () => {
    set({ loading: true });
    await Promise.all([
      get().refreshSettings(),
      get().refreshDailyStatus(),
      get().refreshHealth(),
    ]);
    set({ loading: false });
  },

  saveAll: async () => {
    const { draft } = get();
    if (!draft) return;
    set({ busyAction: "save-settings", error: null });
    try {
      const normalized = {
        ...draft,
        daily_time: normalizeDailyTime(draft.daily_time),
      };
      const updated = await saveSettings(normalized);
      set({ bootstrap: updated, draft: buildDraft(updated) });
      await get().refreshHealth();
      await get().refreshDailyStatus();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ busyAction: "" });
    }
  },

  updateDraft: (patch) => {
    set((state) => ({
      draft: state.draft ? { ...state.draft, ...patch } : null,
    }));
  },

  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));
