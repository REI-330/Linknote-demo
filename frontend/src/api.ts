import type {
  DailyRunStatus,
  EnabledModelRecord,
  HealthBootstrap,
  NoteChatSource,
  NoteDetail,
  ProviderRecord,
  RemoteModelRecord,
  ReportSummary,
  SettingsBootstrap,
  SettingsUpdatePayload
} from "./types";
import { EMPTY_NOTE_DETAIL, EMPTY_REPORT_ITEM } from "./types";

const API_BASE = import.meta.env.DEV ? "http://127.0.0.1:8765/api" : `${window.location.origin}/api`;

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json"
    },
    ...init
  });
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string" && payload.detail.trim()) {
        message = payload.detail.trim();
      }
    } catch {
      // Ignore non-JSON error bodies and fall back to status text.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function asString(value: unknown, fallback = "") {
  return typeof value === "string" ? value : fallback;
}

function asBoolean(value: unknown, fallback = false) {
  return typeof value === "boolean" ? value : fallback;
}

function asNumber(value: unknown, fallback = 0) {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function normalizeReportItem(raw: unknown) {
  const record = asRecord(raw);
  return {
    ...EMPTY_REPORT_ITEM,
    item_id: asString(record.item_id),
    dedupe_key: asString(record.dedupe_key),
    source_url: asString(record.source_url),
    source_title: asString(record.source_title),
    source_context: asString(record.source_context),
    source_origins: asArray<string>(record.source_origins).filter((item) => typeof item === "string"),
    collected_at: asString(record.collected_at),
    status: asString(record.status, "pending"),
    has_note: asBoolean(record.has_note),
    failure_code: asString(record.failure_code),
    failure_title: asString(record.failure_title),
    failure_hint: asString(record.failure_hint),
    versions: asNumber(record.versions),
    detail_path: asString(record.detail_path),
  };
}

function normalizeReportSummary(raw: unknown): ReportSummary {
  const record = asRecord(raw);
  return {
    report_date: asString(record.report_date),
    total_items: asNumber(record.total_items),
    pending_items: asNumber(record.pending_items),
    completed_items: asNumber(record.completed_items),
    failed_items: asNumber(record.failed_items),
    items: asArray(record.items).map(normalizeReportItem),
  };
}

function normalizeHealthBootstrap(raw: unknown): HealthBootstrap {
  const record = asRecord(raw);
  return {
    status: asString(record.status, "warning"),
    checks: asArray(record.checks).map((item) => {
      const check = asRecord(item);
      return {
        key: asString(check.key),
        label: asString(check.label),
        status: asString(check.status, "warning"),
        detail: asString(check.detail),
        code: typeof check.code === "string" ? check.code : undefined,
        followup: typeof check.followup === "string" ? check.followup : undefined,
      };
    }),
  };
}

function normalizeSettingsBootstrap(raw: unknown): SettingsBootstrap {
  const record = asRecord(raw);
  const schedule = asRecord(record.schedule);
  const analysis = asRecord(record.analysis);
  const transcriber = asRecord(record.transcriber);
  const retention = asRecord(record.retention);
  const server = asRecord(record.server);
  const wechat = asRecord(record.wechat);
  const clipboard = asRecord(record.clipboard);
  const bilibili = asRecord(record.bilibili);
  const notification = asRecord(record.notification);
  return {
    note_formats: asArray(record.note_formats).map((item) => {
      const option = asRecord(item);
      return { label: asString(option.label), value: asString(option.value) };
    }),
    note_styles: asArray(record.note_styles).map((item) => {
      const option = asRecord(item);
      return { label: asString(option.label), value: asString(option.value) };
    }),
    providers: asArray(record.providers).map((item) => {
      const provider = asRecord(item);
      return {
        provider_id: asString(provider.provider_id),
        label: asString(provider.label),
        logo: asString(provider.logo, "custom"),
        type: asString(provider.type, "custom"),
        base_url: asString(provider.base_url),
        api_key: asString(provider.api_key),
        api_key_env: asString(provider.api_key_env),
        default_model: asString(provider.default_model),
        models: asArray<string>(provider.models).filter((model) => typeof model === "string"),
        enabled: asBoolean(provider.enabled, true),
      };
    }),
    schedule: {
      enabled: asBoolean(schedule.enabled),
      daily_time: asString(schedule.daily_time),
      auto_collect_wechat: asBoolean(schedule.auto_collect_wechat),
      notify_on_complete: asBoolean(schedule.notify_on_complete),
      autostart_enabled: asBoolean(schedule.autostart_enabled),
    },
    analysis: {
      note_format: asString(analysis.note_format),
      note_style: asString(analysis.note_style),
      enable_source_links: asBoolean(analysis.enable_source_links),
      enable_mind_map: asBoolean(analysis.enable_mind_map),
      enable_ai_chat: asBoolean(analysis.enable_ai_chat),
      enable_screenshots: asBoolean(analysis.enable_screenshots),
      provider_id: asString(analysis.provider_id),
      model_name: asString(analysis.model_name),
    },
    transcriber: {
      type: asString(transcriber.type),
      provider_id: asString(transcriber.provider_id),
      model_name: asString(transcriber.model_name),
      language: asString(transcriber.language),
    },
    retention: {
      days: asNumber(retention.days),
      cleanup_intermediate: asBoolean(retention.cleanup_intermediate),
    },
    server: {
      host: asString(server.host),
      port: asNumber(server.port),
      open_browser: asBoolean(server.open_browser),
      lan_enabled: asBoolean(server.lan_enabled),
    },
    wechat: {
      enabled: asBoolean(wechat.enabled),
      chatlog_root: asString(wechat.chatlog_root),
      account_dir: asString(wechat.account_dir),
      scan_days: asNumber(wechat.scan_days),
      accounts: asArray(wechat.accounts).map((item) => {
        const option = asRecord(item);
        return {
          account_dir: asString(option.account_dir),
          chatlog_root: asString(option.chatlog_root),
          label: asString(option.label),
        };
      }),
    },
    clipboard: {
      enabled: asBoolean(clipboard.enabled),
      include_on_schedule: asBoolean(clipboard.include_on_schedule),
    },
    bilibili: {
      cookies_file: asString(bilibili.cookies_file),
      use_browser_cookies: asBoolean(bilibili.use_browser_cookies),
    },
    notification: {
      enabled: asBoolean(notification.enabled),
      open_target: asString(notification.open_target),
    },
  };
}

function normalizeNoteDetail(raw: unknown): NoteDetail {
  const record = asRecord(raw);
  const item = normalizeReportItem(record.item);
  const media = asRecord(record.media);
  const analysis = asRecord(record.analysis);
  const progress = asRecord(analysis.progress);
  const panels = asRecord(analysis.panels);
  const failure = asRecord(analysis.failure);
  return {
    ...EMPTY_NOTE_DETAIL,
    item,
    media: {
      platform: asString(media.platform),
      video_id: asString(media.video_id),
      canonical_url: asString(media.canonical_url),
      cover_url: asString(media.cover_url),
      duration: asNumber(media.duration),
      uploader: asString(media.uploader),
      description: asString(media.description),
      transcript_source: asString(media.transcript_source),
      tags: asArray<string>(media.tags).filter((tag) => typeof tag === "string"),
    },
    analysis: {
      status: asString(analysis.status, "pending"),
      progress: {
        stage: asString(progress.stage),
        step: asString(progress.step),
        detail: asString(progress.detail),
        started_at: asString(progress.started_at),
        updated_at: asString(progress.updated_at),
      },
      versions: asArray(analysis.versions).map((version) => {
        const item = asRecord(version);
        return {
          version_id: asString(item.version_id),
          label: asString(item.label),
          markdown: asString(item.markdown),
          source_basis: asString(item.source_basis),
          created_at: asString(item.created_at),
          model_name: asString(item.model_name),
          provider_id: asString(item.provider_id),
        };
      }),
      view_modes: asArray<string>(analysis.view_modes).filter((mode) => typeof mode === "string"),
      panels: {
        source_reference: asBoolean(panels.source_reference),
        ai_chat: asBoolean(panels.ai_chat),
      },
      message: asString(analysis.message),
      failure: {
        code: asString(failure.code),
        title: asString(failure.title),
        hint: asString(failure.hint),
        actions: asArray<string>(failure.actions).filter((action) => typeof action === "string"),
      },
      source_reference: asArray(analysis.source_reference).map((segment) => {
        const item = asRecord(segment);
        return {
          start: asNumber(item.start),
          end: asNumber(item.end),
          text: asString(item.text),
          speaker: asString(item.speaker),
        };
      }),
    },
  };
}

export function getTodayReport(): Promise<ReportSummary> {
  return fetchJson("/reports/today").then(normalizeReportSummary);
}

export function getReportByDate(reportDate: string): Promise<ReportSummary> {
  return fetchJson(`/reports/${encodeURIComponent(reportDate)}`).then(normalizeReportSummary);
}

export function getNoteDetail(itemId: string, reportDate?: string): Promise<NoteDetail> {
  const query = reportDate ? `?report_date=${encodeURIComponent(reportDate)}` : "";
  return fetchJson(`/notes/${encodeURIComponent(itemId)}${query}`).then(normalizeNoteDetail);
}

export function deleteFailedReportItem(reportDate: string, itemId: string): Promise<{ deleted: boolean; item_id: string }> {
  return fetchJson(`/reports/${encodeURIComponent(reportDate)}/items/${encodeURIComponent(itemId)}`, {
    method: "DELETE"
  });
}

export function getSettingsBootstrap(): Promise<SettingsBootstrap> {
  return fetchJson("/settings/bootstrap").then(normalizeSettingsBootstrap);
}

export function saveSettings(payload: SettingsUpdatePayload): Promise<SettingsBootstrap> {
  return fetchJson("/settings", {
    method: "POST",
    body: JSON.stringify(payload)
  }).then(normalizeSettingsBootstrap);
}

export function runDailyNow(includeWechat = true, includeClipboard?: boolean): Promise<DailyRunStatus["last_run"]> {
  const search = new URLSearchParams();
  search.set("include_wechat", String(includeWechat));
  if (typeof includeClipboard === "boolean") {
    search.set("include_clipboard", String(includeClipboard));
  }
  return fetchJson(`/daily/run?${search.toString()}`, { method: "POST" });
}

export function getDailyStatus(): Promise<DailyRunStatus> {
  return fetchJson<DailyRunStatus>("/daily/status");
}

export function getHealthBootstrap(): Promise<HealthBootstrap> {
  return fetchJson("/health/bootstrap").then(normalizeHealthBootstrap);
}

export function reanalyzeNote(
  itemId: string,
  reportDate?: string,
  payload?: { provider_id?: string; model_name?: string }
): Promise<{ status: string; versions: number }> {
  const query = reportDate ? `?report_date=${encodeURIComponent(reportDate)}` : "";
  return fetchJson(`/notes/${encodeURIComponent(itemId)}/reanalyze${query}`, {
    method: "POST",
    body: JSON.stringify(payload ?? {})
  });
}

export function analyzeNote(
  itemId: string,
  reportDate?: string,
  payload?: { provider_id?: string; model_name?: string }
): Promise<{ status: string; versions: number }> {
  const query = reportDate ? `?report_date=${encodeURIComponent(reportDate)}` : "";
  return fetchJson(`/notes/${encodeURIComponent(itemId)}/analyze${query}`, {
    method: "POST",
    body: JSON.stringify(payload ?? {})
  });
}

export function askNoteQuestion(
  itemId: string,
  question: string,
  history: Array<{ role: "assistant" | "user"; content: string }>,
  payload?: { provider_id?: string; model_name?: string },
  reportDate?: string
): Promise<{ answer: string; sources?: NoteChatSource[] }> {
  const query = reportDate ? `?report_date=${encodeURIComponent(reportDate)}` : "";
  return fetchJson(`/notes/${encodeURIComponent(itemId)}/chat${query}`, {
    method: "POST",
    body: JSON.stringify({ question, history, ...payload })
  });
}

export function exportNoteUrl(itemId: string, reportDate?: string): string {
  const query = reportDate ? `?report_date=${encodeURIComponent(reportDate)}` : "";
  return `${API_BASE}/notes/${encodeURIComponent(itemId)}/export${query}`;
}

export function ingestClipboard(): Promise<{ path: string; source_type: string }> {
  return fetchJson("/ingest/clipboard", { method: "POST" });
}

export function ingestWechat(forceFullScan = false): Promise<{ created: boolean; path: string }> {
  const query = forceFullScan ? "?force_full_scan=true" : "";
  return fetchJson(`/ingest/wechat${query}`, { method: "POST" });
}

export function ingestManual(text: string, sourceName: string): Promise<{ path: string; source_type: string }> {
  return fetchJson("/ingest/manual", {
    method: "POST",
    body: JSON.stringify({
      text,
      source_name: sourceName
    })
  });
}

export function getProviderList(): Promise<ProviderRecord[]> {
  return fetchJson<ProviderRecord[]>("/get_all_providers");
}

export function getProviderById(providerId: string): Promise<ProviderRecord> {
  return fetchJson<ProviderRecord>(`/get_provider_by_id/${encodeURIComponent(providerId)}`);
}

export function addProvider(payload: {
  name: string;
  api_key: string;
  base_url: string;
  type: string;
}): Promise<{ id: string }> {
  return fetchJson<{ id: string }>("/add_provider", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateProvider(payload: {
  id: string;
  name?: string;
  api_key?: string;
  base_url?: string;
  enabled?: number;
}): Promise<{ id: string }> {
  return fetchJson<{ id: string }>("/update_provider", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function testProviderConnection(providerId: string): Promise<{ status: string }> {
  return fetchJson<{ status: string }>("/connect_test", {
    method: "POST",
    body: JSON.stringify({ id: providerId })
  });
}

export function fetchProviderModels(providerId: string): Promise<{ models: RemoteModelRecord[] }> {
  return fetchJson<{ models: RemoteModelRecord[] }>(`/model_list/${encodeURIComponent(providerId)}`);
}

export function fetchEnabledModels(): Promise<EnabledModelRecord[]> {
  return fetchJson<EnabledModelRecord[]>("/model_list");
}

export function fetchEnabledModelsByProvider(providerId: string): Promise<EnabledModelRecord[]> {
  return fetchJson<EnabledModelRecord[]>(`/model_enable/${encodeURIComponent(providerId)}`);
}

export function addEnabledModel(providerId: string, modelName: string): Promise<{ status: string; model: EnabledModelRecord }> {
  return fetchJson<{ status: string; model: EnabledModelRecord }>("/models", {
    method: "POST",
    body: JSON.stringify({ provider_id: providerId, model_name: modelName })
  });
}

export function deleteEnabledModel(modelId: string): Promise<{ status: string }> {
  return fetchJson<{ status: string }>(`/models/delete/${encodeURIComponent(modelId)}`);
}
