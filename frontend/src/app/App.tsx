import { FormEvent, useEffect, useMemo, useState } from "react";
import { BrowserRouter, useLocation, useNavigate } from "react-router-dom";
import { Suspense, lazy } from "react";
import { useRef } from "react";

// 前端应用壳层：这里负责路由、共享异步状态和跨页面动作，
// 让页面组件尽量只关注渲染本身。

import {
  addEnabledModel,
  addProvider,
  analyzeNote,
  askNoteQuestion,
  deleteFailedReportItem,
  deleteEnabledModel,
  exportNoteUrl,
  fetchEnabledModels,
  fetchEnabledModelsByProvider,
  fetchProviderModels,
  getDailyStatus,
  getHealthBootstrap,
  getNoteDetail,
  getProviderList,
  getReportByDate,
  getSettingsBootstrap,
  getTodayReport,
  ingestClipboard,
  ingestManual,
  ingestWechat,
  reanalyzeNote,
  runDailyNow,
  saveSettings,
  testProviderConnection,
  updateProvider
} from "../api";
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
} from "../types";
import { SettingMenu } from "../pages/SettingPage/Menu";
import { SettingLayout } from "../layouts/SettingLayout";
const AnalysisSettingsPage = lazy(() => import("../pages/SettingPage/Analysis"));
const NoteDetailPage = lazy(() => import("../pages/NotePage/Detail").then((module) => ({ default: module.NoteDetailPage })));
const DailyReportPage = lazy(() => import("../pages/ReportPage/DailyReport").then((module) => ({ default: module.DailyReportPage })));
const MarkdownViewer = lazy(() => import("../pages/HomePage/components/MarkdownViewer"));
const ModelSettingsPage = lazy(() => import("../pages/SettingPage/Model"));
const DownloaderPage = lazy(() => import("../pages/SettingPage/Downloader"));
const MonitorPage = lazy(() => import("../pages/SettingPage/Monitor"));
const TranscriberPage = lazy(() => import("../pages/SettingPage/transcriber"));

type WorkspaceMode = "markdown" | "mindmap";
type ChatPanelMode = false | "half" | "full";
type SettingsSection = "analysis" | "model" | "transcriber" | "download" | "monitor";
type ChatMessage = {
  role: "assistant" | "user";
  content: string;
  sources?: NoteChatSource[];
};
type AnalysisTarget = EnabledModelRecord & {
  label: string;
  providerLabel: string;
};
type ProviderEditor = ProviderRecord & {
  remoteModels: RemoteModelRecord[];
  remoteModelName: string;
  manualModelName: string;
  isLoadingModels: boolean;
  isSaving: boolean;
  isTesting: boolean;
  isAddingModel: boolean;
};
type NewProviderDraft = {
  name: string;
  base_url: string;
  api_key: string;
};
type HealthCheck = HealthBootstrap["checks"][number];
type ProviderWithModels = {
  provider_id: string;
  default_model: string;
  models: string[];
};

const statusLabel: Record<string, string> = {
  pending: "待分析",
  running: "分析中",
  completed: "已完成",
  failed: "失败"
};

const settingsSections: Array<{ id: SettingsSection; title: string; subtitle: string }> = [
  { id: "analysis", title: "分析设置", subtitle: "笔记风格、输出格式与展示能力" },
  { id: "model", title: "AI 模型设置", subtitle: "提供商、模型与 API Key" },
  { id: "transcriber", title: "音频转写配置", subtitle: "转写方式与转写模型" },
  { id: "download", title: "下载配置", subtitle: "B 站 cookies 与来源采集" },
  { id: "monitor", title: "部署监控", subtitle: "健康检查与最近运行状态" }
];

const assistantGreeting = "这里会基于当前笔记、原文片段和视频信息继续回答问题。";

function PageFallback() {
  return (
    <div className="bn-empty-box">
      <div>
        <strong>页面加载中</strong>
        <p>正在准备当前视图所需的模块。</p>
      </div>
    </div>
  );
}

function normalizeDailyTime(value?: string) {
  const match = /^(\d{1,2}):(\d{1,2})$/.exec((value ?? "").trim());
  if (!match) {
    return "21:00";
  }
  const hour = Number(match[1]);
  const minute = Number(match[2]);
  if (!Number.isInteger(hour) || !Number.isInteger(minute) || hour < 0 || hour > 23 || minute < 0 || minute > 59) {
    return "21:00";
  }
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function buildInitialSettings(bootstrap: SettingsBootstrap | null): SettingsUpdatePayload | null {
  if (!bootstrap) {
    return null;
  }
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
    providers: bootstrap.providers.map((provider) => ({ ...provider }))
  };
}

function toBootstrapProvider(provider: ProviderRecord): SettingsBootstrap["providers"][number] {
  return {
    provider_id: provider.provider_id,
    label: provider.label,
    logo: provider.logo,
    type: provider.type,
    base_url: provider.base_url,
    api_key: provider.api_key,
    api_key_env: provider.api_key_env,
    default_model: provider.default_model,
    models: [...provider.models],
    enabled: provider.enabled
  };
}

function toSettingsProvider(provider: ProviderRecord): SettingsUpdatePayload["providers"][number] {
  return { ...toBootstrapProvider(provider) };
}

function mergeProviderEditors(records: ProviderRecord[], current: ProviderEditor[]): ProviderEditor[] {
  return records.map((record) => {
    const previous = current.find((item) => item.provider_id === record.provider_id);
    return {
      ...record,
      remoteModels: previous?.remoteModels ?? [],
      remoteModelName: previous?.remoteModelName ?? "",
      manualModelName: previous?.manualModelName ?? "",
      isLoadingModels: false,
      isSaving: false,
      isTesting: false,
      isAddingModel: false
    };
  });
}

function normalizeModelNameList(modelNames: string[]) {
  const normalized: string[] = [];
  for (const modelName of modelNames) {
    const cleanName = modelName.trim();
    if (cleanName && !normalized.includes(cleanName)) {
      normalized.push(cleanName);
    }
  }
  return normalized;
}

function addModelToProviderState<T extends ProviderWithModels>(provider: T, modelName: string): T {
  const cleanName = modelName.trim();
  if (!cleanName) {
    return provider;
  }
  return {
    ...provider,
    default_model: provider.default_model.trim() || cleanName,
    models: normalizeModelNameList([...provider.models, cleanName])
  };
}

function removeModelFromProviderState<T extends ProviderWithModels>(provider: T, modelName: string): T {
  const cleanName = modelName.trim();
  if (!cleanName) {
    return provider;
  }
  const nextModels = normalizeModelNameList(provider.models.filter((name) => name.trim() !== cleanName));
  const nextDefaultModel = provider.default_model.trim() === cleanName ? nextModels[0] ?? "" : provider.default_model;
  return {
    ...provider,
    default_model: nextDefaultModel,
    models: nextModels
  };
}

function upsertEnabledModelRecord(records: EnabledModelRecord[], model: EnabledModelRecord) {
  const cleanProviderId = model.provider_id.trim();
  const cleanModelName = model.model_name.trim();
  const cleanId = model.id.trim() || buildAnalysisTargetId(cleanProviderId, cleanModelName);
  if (!cleanProviderId || !cleanModelName) {
    return records;
  }
  const nextRecord = {
    id: cleanId,
    provider_id: cleanProviderId,
    model_name: cleanModelName
  };
  const nextRecords = records.filter(
    (item) => !(item.provider_id.trim() === cleanProviderId && item.model_name.trim() === cleanModelName)
  );
  nextRecords.push(nextRecord);
  return nextRecords;
}

function removeEnabledModelRecord(records: EnabledModelRecord[], modelId: string) {
  return records.filter((item) => item.id !== modelId);
}

function buildAnalysisTargetId(providerId: string, modelName: string) {
  return `${providerId}:${modelName}`;
}

function buildHealthCheckMap(health: HealthBootstrap | null) {
  return (health?.checks ?? []).reduce<Record<string, HealthCheck>>((result, check) => {
    result[check.key] = check;
    return result;
  }, {});
}

function formatDuration(seconds: number) {
  if (!seconds) {
    return "";
  }
  const totalSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(totalSeconds / 60);
  const remainSeconds = totalSeconds % 60;
  const hours = Math.floor(minutes / 60);
  const remainMinutes = minutes % 60;
  if (hours > 0) {
    return `${hours}:${String(remainMinutes).padStart(2, "0")}:${String(remainSeconds).padStart(2, "0")}`;
  }
  return `${remainMinutes}:${String(remainSeconds).padStart(2, "0")}`;
}

function formatTimestamp(value?: string) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", {
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function getHealthFollowup(check: HealthBootstrap["checks"][number]) {
  if (check.followup?.trim()) {
    return check.followup.trim();
  }
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

function getProviderAuthBlockReason(check?: HealthBootstrap["checks"][number]) {
  if (!check || check.status === "ok") {
    return null;
  }
  if (check.code === "invalid_api_key") {
    return "当前模型 API Key 无效，先到设置页修正后再分析。";
  }
  return null;
}

function getProviderBrand(provider?: Partial<ProviderRecord> | Partial<ProviderEditor> | null) {
  return {
    label: provider?.label || provider?.name || provider?.provider_id || "Custom",
    icon: provider?.logo || "custom"
  };
}

function LinknoteShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const initialReportDate = searchParams.get("report_date")?.trim() ?? "";
  const routeSegments = useMemo(() => location.pathname.split("/").filter(Boolean), [location.pathname]);
  const isSettingsView = routeSegments[0] === "settings";
  const noteRouteItemId = routeSegments[0] === "notes" ? routeSegments[1] ?? "" : "";
  const isNoteView = routeSegments[0] === "notes" && Boolean(noteRouteItemId);
  const routeSection = useMemo<SettingsSection>(() => {
    if (!isSettingsView) {
      return "analysis";
    }
    const maybeSection = routeSegments[1];
    if (settingsSections.some((item) => item.id === maybeSection)) {
      return maybeSection as SettingsSection;
    }
    return "analysis";
  }, [isSettingsView, routeSegments]);

  const [reportDate, setReportDate] = useState(initialReportDate);
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [detail, setDetail] = useState<NoteDetail | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [bootstrap, setBootstrap] = useState<SettingsBootstrap | null>(null);
  const [settingsDraft, setSettingsDraft] = useState<SettingsUpdatePayload | null>(null);
  const [providerEditors, setProviderEditors] = useState<ProviderEditor[]>([]);
  const [enabledModels, setEnabledModels] = useState<EnabledModelRecord[]>([]);
  const [newProviderDraft, setNewProviderDraft] = useState<NewProviderDraft>({
    name: "",
    base_url: "",
    api_key: ""
  });
  const [dailyStatus, setDailyStatus] = useState<DailyRunStatus | null>(null);
  const [health, setHealth] = useState<HealthBootstrap | null>(null);
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>("markdown");
  const [showSourceReference, setShowSourceReference] = useState(false);
  const [chatPanelMode, setChatPanelMode] = useState<ChatPanelMode>(false);
  const [manualUrl, setManualUrl] = useState("");
  const [busyAction, setBusyAction] = useState("");
  const [errorText, setErrorText] = useState("");
  const [dismissedSetupHintsSignature, setDismissedSetupHintsSignature] = useState("");
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([{ role: "assistant", content: assistantGreeting }]);
  const [selectedVersionId, setSelectedVersionId] = useState("");
  const [copiedMarkdown, setCopiedMarkdown] = useState(false);
  const detailUiHydratedKeyRef = useRef("");
  const healthChecks = useMemo(() => buildHealthCheckMap(health), [health]);
  const activeSettingsSection = routeSection;
  const modelRouteTarget = activeSettingsSection === "model" ? routeSegments[2] ?? "" : "";
  const isCreatingProvider = modelRouteTarget === "new";
  const activeProviderId = !isCreatingProvider && activeSettingsSection === "model" ? modelRouteTarget : "";
  const activeItemId = isNoteView ? noteRouteItemId : "";

  const selectedItem = useMemo(
    () => report?.items.find((item) => item.item_id === activeItemId) ?? null,
    [activeItemId, report]
  );
  const analysisTargets = useMemo<AnalysisTarget[]>(
    () =>
      enabledModels.map((model) => {
        const provider = providerEditors.find((item) => item.provider_id === model.provider_id);
        const providerLabel = provider?.label ?? model.provider_id;
        return {
          ...model,
          label: `${providerLabel} / ${model.model_name}`,
          providerLabel
        };
      }),
    [enabledModels, providerEditors]
  );
  const draftAnalysisTargetId =
    settingsDraft?.analysis_provider_id && settingsDraft.analysis_model_name
      ? buildAnalysisTargetId(settingsDraft.analysis_provider_id, settingsDraft.analysis_model_name)
      : "";
  const configuredAnalysisTargetId =
    bootstrap?.analysis.provider_id && bootstrap.analysis.model_name
      ? buildAnalysisTargetId(bootstrap.analysis.provider_id, bootstrap.analysis.model_name)
      : "";
  const selectedAnalysisTarget = useMemo(
    () => analysisTargets.find((target) => target.id === configuredAnalysisTargetId) ?? null,
    [analysisTargets, configuredAnalysisTargetId]
  );
  const selectedProvider = useMemo(
    () =>
      selectedAnalysisTarget
        ? providerEditors.find((provider) => provider.provider_id === selectedAnalysisTarget.provider_id) ?? null
        : null,
    [providerEditors, selectedAnalysisTarget]
  );
  const previewVersion = useMemo(
    () => detail?.analysis.versions.find((version) => version.version_id === selectedVersionId) ?? detail?.analysis.versions[0] ?? null,
    [detail, selectedVersionId]
  );
  const activeProvider = useMemo(
    () => (activeProviderId ? providerEditors.find((item) => item.provider_id === activeProviderId) ?? null : null),
    [activeProviderId, providerEditors]
  );
  const providerMenuItems = useMemo(
    () =>
      providerEditors.map((provider) => ({
        key: provider.provider_id,
        provider
      })),
    [providerEditors]
  );
  const activeProviderModels = useMemo(
    () => enabledModels.filter((item) => item.provider_id === activeProvider?.provider_id),
    [activeProvider, enabledModels]
  );
  const selectedTargetAiBlockReason = useMemo(() => {
    if (!bootstrap || !settingsDraft) {
      return null;
    }
    if (!analysisTargets.length) {
      return "当前还没有启用模型，先到设置页为 provider 添加至少一个可用模型。";
    }
    if (!bootstrap.analysis.provider_id || !bootstrap.analysis.model_name) {
      return "当前还没有在设置页选定分析模型，先到设置页选择并保存。";
    }
    if (!selectedProvider) {
      return "设置页当前选中的分析模型不存在或未启用，先修正后再分析。";
    }
    if (!selectedProvider.enabled) {
      return "设置页当前选中的 provider 已禁用，先到设置页启用后再分析。";
    }
    if (!selectedProvider.api_key && !selectedProvider.api_key_env) {
      return "当前分析模型对应的 provider 还没有 API Key，先到设置页填写后再分析。";
    }
    return getProviderAuthBlockReason(healthChecks.provider_auth);
  }, [analysisTargets.length, bootstrap, healthChecks.provider_auth, selectedProvider, settingsDraft]);
  const wechatBlockReason = useMemo(() => {
    if (!settingsDraft) {
      return null;
    }
    if (!settingsDraft.wechat_enabled) {
      return "微信采集已关闭，先到设置页启用微信采集。";
    }
    if (!healthChecks.wechat_root || healthChecks.wechat_root.status !== "ok") {
      return "当前 WeChat 数据目录不可用，先检查设置页里的 chatlog 路径。";
    }
    return null;
  }, [healthChecks, settingsDraft]);
  const clipboardBlockReason = useMemo(() => {
    if (!settingsDraft) {
      return null;
    }
    return settingsDraft.clipboard_enabled ? null : "剪贴板采集已关闭，先到设置页启用后再读取。";
  }, [settingsDraft]);
  const dailyRunBlockReason = useMemo(
    () => selectedTargetAiBlockReason ?? wechatBlockReason,
    [selectedTargetAiBlockReason, wechatBlockReason]
  );
  const chatBlockReason = useMemo(() => {
    if (!settingsDraft) {
      return null;
    }
    if (!settingsDraft.enable_ai_chat) {
      return "AI 问答已关闭，先到设置页开启后再追问。";
    }
    return selectedTargetAiBlockReason;
  }, [selectedTargetAiBlockReason, settingsDraft]);
  const selectedTargetSetupHints = useMemo(() => {
    const hints: string[] = [];
    if (!analysisTargets.length) {
      hints.push("先到设置页添加一个模型提供商，并为它启用至少一个模型。");
    }
    if (analysisTargets.length && (!bootstrap?.analysis.provider_id || !bootstrap.analysis.model_name)) {
      hints.push("设置页里必须明确选择一个分析模型；系统不再自动挑选第一个可用模型。");
    }
    if (selectedProvider && !selectedProvider.api_key && !selectedProvider.api_key_env) {
      hints.push(`当前模型 ${selectedProvider.label} 缺少 API Key，请先在设置页填写。`);
    }
    if (healthChecks.provider_auth?.code === "invalid_api_key") {
      hints.push("当前 API Key 已配置，但实时鉴权失败，请修正后再分析。");
    }
    if (
      healthChecks.bilibili_cookies &&
      healthChecks.bilibili_cookies.status === "ok" &&
      healthChecks.bilibili_cookies.detail.includes("public videos only")
    ) {
      hints.push("公开视频可以直接分析；受限视频请提供 cookies.txt 或启用 browser cookies fallback。");
    }
    return hints;
  }, [analysisTargets.length, bootstrap, healthChecks, selectedProvider]);
  const setupHintsSignature = selectedTargetSetupHints.join("\n");
  const showSetupBanner = !isSettingsView && selectedTargetSetupHints.length > 0 && dismissedSetupHintsSignature !== setupHintsSignature;
  const hasBackgroundWork = Boolean(
    busyAction === "daily-run" || report?.items.some((item) => item.status === "pending" || item.status === "running")
  );

  async function refreshReport() {
    setLoadingReport(true);
    try {
      const nextReport = reportDate ? await getReportByDate(reportDate) : await getTodayReport();
      setReport(nextReport);
      if (nextReport.report_date !== reportDate) {
        setReportDate(nextReport.report_date);
      }
    } finally {
      setLoadingReport(false);
    }
  }

  async function refreshSettings() {
    const nextBootstrap = await getSettingsBootstrap();
    setBootstrap(nextBootstrap);
    setSettingsDraft(buildInitialSettings(nextBootstrap));
  }

  async function refreshProviderCatalog() {
    const [nextProviders, nextModels] = await Promise.all([getProviderList(), fetchEnabledModels()]);
    setProviderEditors((current) => mergeProviderEditors(nextProviders, current));
    setEnabledModels(nextModels);
    setBootstrap((current) =>
      current
        ? {
            ...current,
            providers: nextProviders.map((provider) => toBootstrapProvider(provider))
          }
        : current
    );
    setSettingsDraft((current) =>
      current
        ? {
            ...current,
            providers: nextProviders.map((provider) => toSettingsProvider(provider))
          }
        : current
    );
  }

  async function refreshDailyStatus() {
    const nextStatus = await getDailyStatus();
    setDailyStatus(nextStatus);
  }

  async function refreshHealth() {
    const nextHealth = await getHealthBootstrap();
    setHealth(nextHealth);
  }

  async function refreshModelConfiguration() {
    await refreshSettings();
    await refreshProviderCatalog();
    await refreshHealth();
  }

  function onSelectAnalysisTarget(targetId: string) {
    const target = analysisTargets.find((item) => item.id === targetId);
    setSettingsDraft((current) =>
      current
        ? {
            ...current,
            analysis_provider_id: target?.provider_id ?? "",
            analysis_model_name: target?.model_name ?? ""
          }
        : current
    );
  }

  useEffect(() => {
    void refreshReport().catch((error: Error) => setErrorText(error.message));
    void refreshSettings().catch((error: Error) => setErrorText(error.message));
    void refreshProviderCatalog().catch((error: Error) => setErrorText(error.message));
    void refreshDailyStatus().catch((error: Error) => setErrorText(error.message));
    void refreshHealth().catch((error: Error) => setErrorText(error.message));
  }, [reportDate]);

  useEffect(() => {
    setErrorText("");
  }, [location.pathname, location.search]);

  useEffect(() => {
    if (!errorText) {
      return;
    }
    const timer = window.setTimeout(() => setErrorText(""), 4800);
    return () => window.clearTimeout(timer);
  }, [errorText]);

  useEffect(() => {
    if (!selectedTargetSetupHints.length) {
      setDismissedSetupHintsSignature("");
    }
  }, [selectedTargetSetupHints]);

  useEffect(() => {
    if (!activeItemId || !report) {
      setDetail(null);
      setLoadingDetail(false);
      return;
    }
    const shouldShowDetailLoading = !detail || detail.item.item_id !== activeItemId;
    if (shouldShowDetailLoading) {
      setLoadingDetail(true);
    }
    void getNoteDetail(activeItemId, report.report_date)
      .then(setDetail)
      .catch((error: Error) => setErrorText(error.message))
      .finally(() => {
        if (shouldShowDetailLoading) {
          setLoadingDetail(false);
        }
      });
  }, [activeItemId, detail?.item.item_id, report?.report_date, selectedItem?.status]);

  useEffect(() => {
    if (!detail || !report || !selectedItem || busyAction !== "") {
      return;
    }
    if (selectedItem.status !== "pending") {
      return;
    }
    if (detail.analysis.status !== "pending" || detail.analysis.versions.length > 0) {
      return;
    }
    if (selectedTargetAiBlockReason) {
      return;
    }
    void runAction("analyze", () => analyzeNote(detail.item.item_id, report.report_date));
  }, [busyAction, detail, report, selectedItem, selectedTargetAiBlockReason]);

  useEffect(() => {
    setChatQuestion("");
    setChatMessages([{ role: "assistant", content: assistantGreeting }]);
    detailUiHydratedKeyRef.current = "";
  }, [activeItemId]);

  useEffect(() => {
    setSelectedVersionId((current) => {
      const versions = detail?.analysis.versions ?? [];
      if (current && versions.some((version) => version.version_id === current)) {
        return current;
      }
      return versions[0]?.version_id ?? "";
    });
  }, [detail]);

  useEffect(() => {
    if (!detail) {
      return;
    }
    const hydrateKey = detail.item.item_id;
    if (detailUiHydratedKeyRef.current === hydrateKey) {
      return;
    }
    detailUiHydratedKeyRef.current = hydrateKey;
    setShowSourceReference(Boolean(detail.analysis.panels?.source_reference));
    setChatPanelMode(Boolean(detail.analysis.panels?.ai_chat) && settingsDraft?.enable_ai_chat ? "half" : false);
  }, [detail, settingsDraft?.enable_ai_chat]);

  useEffect(() => {
    if (settingsDraft?.enable_ai_chat === false) {
      setChatPanelMode(false);
    }
  }, [settingsDraft?.enable_ai_chat]);

  useEffect(() => {
    if (!hasBackgroundWork) {
      return;
    }
    const timer = window.setInterval(() => {
      void refreshReport().catch(() => undefined);
      void refreshDailyStatus().catch(() => undefined);
    }, 4000);
    return () => window.clearInterval(timer);
  }, [hasBackgroundWork, reportDate]);

  useEffect(() => {
    setCopiedMarkdown(false);
  }, [selectedVersionId, activeItemId]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (reportDate) {
      params.set("report_date", reportDate);
    } else {
      params.delete("report_date");
    }
    const nextSearch = params.toString();
    const currentSearch = location.search.startsWith("?") ? location.search.slice(1) : location.search;
    if (nextSearch !== currentSearch) {
      navigate(
        {
          pathname: location.pathname,
          search: nextSearch ? `?${nextSearch}` : ""
        },
        { replace: true }
      );
    }
  }, [location.pathname, location.search, navigate, reportDate]);

  async function runAction(name: string, action: () => Promise<unknown>) {
    setBusyAction(name);
    setErrorText("");
    try {
      await action();
      await refreshReport();
      await refreshProviderCatalog();
      await refreshDailyStatus();
      await refreshHealth();
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "Unknown error");
    } finally {
      setBusyAction("");
    }
  }

  async function askQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedItem || !report || !chatQuestion.trim()) {
      return;
    }
    if (chatBlockReason) {
      setErrorText(chatBlockReason);
      setChatMessages((current) => [...current, { role: "assistant", content: chatBlockReason }]);
      return;
    }
    const question = chatQuestion.trim();
    setChatMessages((current) => [...current, { role: "user", content: question }]);
    setChatQuestion("");
    setBusyAction("chat");
    setErrorText("");
    try {
      const history = chatMessages
        .filter((message) => message.role === "assistant" || message.role === "user")
        .map((message) => ({ role: message.role, content: message.content }));
      const response = await askNoteQuestion(
        selectedItem.item_id,
        question,
        history,
        undefined,
        report.report_date
      );
      setChatMessages((current) => [
        ...current,
        { role: "assistant", content: response.answer, sources: response.sources ?? [] }
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setErrorText(message);
      setChatMessages((current) => [...current, { role: "assistant", content: `问答失败：${message}` }]);
    } finally {
      setBusyAction("");
    }
  }

  async function saveAllSettings() {
    if (!settingsDraft) {
      return;
    }
    const normalizedDraft = {
      ...settingsDraft,
      daily_time: normalizeDailyTime(settingsDraft.daily_time),
    };
    setBusyAction("save-settings");
    setErrorText("");
    try {
      const updated = await saveSettings(normalizedDraft);
      setBootstrap(updated);
      setSettingsDraft(buildInitialSettings(updated));
      await refreshProviderCatalog();
      await refreshDailyStatus();
      await refreshHealth();
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "Unknown error");
    } finally {
      setBusyAction("");
    }
  }

  function updateSettingsDraft(patch: Partial<SettingsUpdatePayload>) {
    setSettingsDraft((current) => (current ? { ...current, ...patch } : current));
  }

  function updateProviderEditor(
    providerId: string,
    patch: Partial<ProviderEditor> | ((current: ProviderEditor) => Partial<ProviderEditor>)
  ) {
    setProviderEditors((current) =>
      current.map((provider) => {
        if (provider.provider_id !== providerId) {
          return provider;
        }
        const nextPatch = typeof patch === "function" ? patch(provider) : patch;
        return { ...provider, ...nextPatch };
      })
    );
  }

  function applyEnabledModelAdd(model: EnabledModelRecord) {
    const cleanProviderId = model.provider_id.trim();
    const cleanModelName = model.model_name.trim();
    if (!cleanProviderId || !cleanModelName) {
      return;
    }
    setEnabledModels((current) => upsertEnabledModelRecord(current, model));
    updateProviderEditor(cleanProviderId, (current) => {
      const nextRemoteModels = current.remoteModels.filter((item) => item.id.trim() !== cleanModelName);
      const nextRemoteModelName =
        current.remoteModelName.trim() === cleanModelName ? nextRemoteModels[0]?.id ?? "" : current.remoteModelName;
      return {
        ...addModelToProviderState(current, cleanModelName),
        remoteModels: nextRemoteModels,
        remoteModelName: nextRemoteModelName,
        manualModelName: ""
      };
    });
    setBootstrap((current) =>
      current
        ? {
            ...current,
            providers: current.providers.map((provider) =>
              provider.provider_id === cleanProviderId ? addModelToProviderState(provider, cleanModelName) : provider
            )
          }
        : current
    );
    setSettingsDraft((current) =>
      current
        ? {
            ...current,
            providers: current.providers.map((provider) =>
              provider.provider_id === cleanProviderId ? addModelToProviderState(provider, cleanModelName) : provider
            )
          }
        : current
    );
  }

  function applyEnabledModelDelete(modelId: string, providerId: string) {
    const cleanProviderId = providerId.trim();
    const separatorIndex = modelId.indexOf(":");
    const modelName = separatorIndex >= 0 ? modelId.slice(separatorIndex + 1) : "";
    const cleanModelName = modelName.trim();
    if (!cleanProviderId || !cleanModelName) {
      setEnabledModels((current) => removeEnabledModelRecord(current, modelId));
      return;
    }
    setEnabledModels((current) => removeEnabledModelRecord(current, modelId));
    updateProviderEditor(cleanProviderId, (current) => ({
      ...removeModelFromProviderState(current, cleanModelName)
    }));
    setBootstrap((current) =>
      current
        ? {
            ...current,
            providers: current.providers.map((provider) =>
              provider.provider_id === cleanProviderId ? removeModelFromProviderState(provider, cleanModelName) : provider
            )
          }
        : current
    );
    setSettingsDraft((current) =>
      current
        ? {
            ...current,
            providers: current.providers.map((provider) =>
              provider.provider_id === cleanProviderId ? removeModelFromProviderState(provider, cleanModelName) : provider
            )
          }
        : current
    );
  }

  async function persistProviderDraft(provider: ProviderEditor) {
    await updateProvider({
      id: provider.provider_id,
      name: provider.label.trim(),
      api_key: provider.api_key.trim(),
      base_url: provider.base_url.trim(),
      enabled: provider.enabled ? 1 : 0
    });
  }

  async function onSaveProvider(providerId: string) {
    const provider = providerEditors.find((item) => item.provider_id === providerId);
    if (!provider) {
      return;
    }
    updateProviderEditor(providerId, { isSaving: true });
    setErrorText("");
    try {
      await persistProviderDraft(provider);
      await refreshModelConfiguration();
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "Unknown error");
    } finally {
      updateProviderEditor(providerId, { isSaving: false });
    }
  }

  async function onTestProvider(providerId: string) {
    const provider = providerEditors.find((item) => item.provider_id === providerId);
    if (!provider) {
      return;
    }
    updateProviderEditor(providerId, { isTesting: true });
    setErrorText("");
    try {
      await persistProviderDraft(provider);
      await testProviderConnection(providerId);
      await refreshModelConfiguration();
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "Unknown error");
    } finally {
      updateProviderEditor(providerId, { isTesting: false });
    }
  }

  async function onLoadProviderModels(providerId: string) {
    const provider = providerEditors.find((item) => item.provider_id === providerId);
    if (!provider) {
      return;
    }
    updateProviderEditor(providerId, { isLoadingModels: true });
    setErrorText("");
    try {
      await persistProviderDraft(provider);
      await refreshSettings();
      const [response, providerEnabledModels] = await Promise.all([
        fetchProviderModels(providerId),
        fetchEnabledModelsByProvider(providerId)
      ]);
      const enabledNames = new Set(
        providerEnabledModels.map((item) => item.model_name.trim())
      );
      const availableModels = response.models.filter((model) => !enabledNames.has(model.id.trim()));
      updateProviderEditor(providerId, {
        isLoadingModels: false,
        remoteModels: availableModels,
        remoteModelName: availableModels[0]?.id ?? ""
      });
      await refreshProviderCatalog();
      await refreshHealth();
    } catch (error) {
      updateProviderEditor(providerId, { isLoadingModels: false });
      setErrorText(error instanceof Error ? error.message : "Unknown error");
    }
  }

  async function onAddProviderModel(providerId: string) {
    const provider = providerEditors.find((item) => item.provider_id === providerId);
    if (!provider) {
      return;
    }
    const modelName = (provider.manualModelName || provider.remoteModelName).trim();
    if (!modelName) {
      setErrorText("先选择远端模型，或手动填写模型名。");
      return;
    }
    const enabledNames = new Set(
      enabledModels
        .filter((item) => item.provider_id === providerId)
        .map((item) => item.model_name.trim())
    );
    if (enabledNames.has(modelName)) {
      setErrorText("这个模型已经在当前提供商里启用了，不需要重复保存。");
      return;
    }
    updateProviderEditor(providerId, { isAddingModel: true });
    setErrorText("");
    try {
      const response = await addEnabledModel(providerId, modelName);
      applyEnabledModelAdd(response.model);
      await refreshHealth();
      updateProviderEditor(providerId, {
        isAddingModel: false
      });
    } catch (error) {
      updateProviderEditor(providerId, { isAddingModel: false });
      setErrorText(error instanceof Error ? error.message : "Unknown error");
    }
  }

  async function onDeleteProviderModel(modelId: string, providerId: string) {
    updateProviderEditor(providerId, { isAddingModel: true });
    setErrorText("");
    try {
      await deleteEnabledModel(modelId);
      applyEnabledModelDelete(modelId, providerId);
      await refreshSettings();
      await refreshHealth();
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "Unknown error");
    } finally {
      updateProviderEditor(providerId, { isAddingModel: false });
    }
  }

  async function onCreateProvider(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newProviderDraft.name.trim() || !newProviderDraft.base_url.trim()) {
      setErrorText("新增 provider 需要至少填写名称和 Base URL。");
      return;
    }
    setBusyAction("create-provider");
    setErrorText("");
    try {
      const response = await addProvider({
        name: newProviderDraft.name.trim(),
        api_key: newProviderDraft.api_key.trim(),
        base_url: newProviderDraft.base_url.trim(),
        type: "custom"
      });
      setNewProviderDraft({ name: "", base_url: "", api_key: "" });
      await refreshProviderCatalog();
      await refreshHealth();
      openProviderEditor(response.id);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "Unknown error");
    } finally {
      setBusyAction("");
    }
  }

  async function removeFailedReportItem(itemId: string) {
    if (!report) {
      return;
    }
    const item = report.items.find((current) => current.item_id === itemId);
    if (!item || item.status !== "failed") {
      return;
    }
    const confirmed = window.confirm(`删除这条失败记录后，它会从 ${report.report_date} 的卡片流中隐藏。继续吗？`);
    if (!confirmed) {
      return;
    }
    await runAction(`delete-failed:${itemId}`, () => deleteFailedReportItem(report.report_date, itemId));
  }

  function navigateWithSearch(pathname: string) {
    const params = new URLSearchParams(location.search);
    navigate({
      pathname,
      search: params.toString() ? `?${params.toString()}` : ""
    });
  }

  function openProviderEditor(providerId: string) {
    navigateWithSearch(`/settings/model/${providerId}`);
  }

  function openNewProviderForm() {
    setNewProviderDraft({ name: "", base_url: "", api_key: "" });
    navigateWithSearch("/settings/model/new");
  }

  function selectProviderMenuItem(provider: ProviderEditor) {
    openProviderEditor(provider.provider_id);
  }

  function openSettings(section: SettingsSection = "analysis") {
    navigateWithSearch(`/settings/${section}`);
  }

  function openHome() {
    navigateWithSearch("/");
  }

  function openNote(itemId: string) {
    navigateWithSearch(`/notes/${itemId}`);
  }

  function clearChatMessages() {
    setChatMessages([{ role: "assistant", content: assistantGreeting }]);
  }

  async function submitPrimaryAction() {
    if (selectedItem && report) {
      if (selectedTargetAiBlockReason) {
        setErrorText(selectedTargetAiBlockReason);
        return;
      }
      await runAction("reanalyze", () => reanalyzeNote(selectedItem.item_id, report.report_date));
      return;
    }
    if (!manualUrl.trim()) {
      setErrorText("先填入视频链接。");
      return;
    }
    await runAction("manual", () => ingestManual(manualUrl.trim(), "manual-bilibili"));
    setManualUrl("");
  }

  function onExportMarkdown() {
    if (!selectedItem || !report || !previewVersion) {
      return;
    }
    window.open(exportNoteUrl(selectedItem.item_id, report.report_date), "_blank", "noopener,noreferrer");
  }

  async function copyMarkdown() {
    if (!previewVersion) {
      return;
    }
    try {
      await navigator.clipboard.writeText(previewVersion.markdown);
      setCopiedMarkdown(true);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "复制失败");
    }
  }

  const workspaceTitle = selectedItem?.source_title ?? "选择一条笔记";
  const selectedStyleLabel =
    bootstrap?.note_styles.find((item) => item.value === settingsDraft?.note_style)?.label ?? settingsDraft?.note_style ?? "默认";
  const selectedProviderSummary = previewVersion?.provider_id
    ? `${providerEditors.find((provider) => provider.provider_id === previewVersion.provider_id)?.label ?? previewVersion.provider_id} / ${previewVersion.model_name ?? ""}`
    : selectedProvider
      ? `${selectedProvider.label} / ${selectedAnalysisTarget?.model_name ?? ""}`
      : "未选择";
  const activeProviderBrand = activeProvider ? getProviderBrand(activeProvider) : null;
  const effectiveWechatScanDays = settingsDraft?.wechat_scan_days ?? bootstrap?.wechat.scan_days ?? 3;

  const noteDetailView = (
    <NoteDetailPage
      sourceUrl={selectedItem?.source_url}
      onBackHome={openHome}
      onOpenSettings={() => openSettings("analysis")}
      preview={
        <MarkdownViewer
          selectedItem={selectedItem}
          loadingDetail={loadingDetail}
          detail={detail}
          selectedVersionId={selectedVersionId}
          onSelectVersion={setSelectedVersionId}
          previewVersion={previewVersion}
          workspaceMode={workspaceMode}
          onToggleWorkspaceMode={() => setWorkspaceMode(workspaceMode === "markdown" ? "mindmap" : "markdown")}
          copiedMarkdown={copiedMarkdown}
          onCopyMarkdown={() => void copyMarkdown()}
          onExportMarkdown={onExportMarkdown}
          showSourceReference={showSourceReference}
          onToggleSourceReference={() => setShowSourceReference((current) => !current)}
          chatPanelMode={chatPanelMode}
          onToggleChatPanel={() => setChatPanelMode((current) => (current ? false : "half"))}
          onChangeChatPanelMode={(mode) => setChatPanelMode(mode)}
          aiChatEnabled={Boolean(settingsDraft?.enable_ai_chat)}
          formatTimestamp={formatTimestamp}
          formatDuration={formatDuration}
          workspaceTitle={workspaceTitle}
          selectedProviderSummary={selectedProviderSummary}
          selectedStyleLabel={selectedStyleLabel}
          busyAction={busyAction}
          selectedTargetAiBlockReason={selectedTargetAiBlockReason}
          onSubmitPrimaryAction={() => void submitPrimaryAction()}
          onOpenSettings={() => openSettings("model")}
          chatMessages={chatMessages}
          chatQuestion={chatQuestion}
          onChatQuestionChange={setChatQuestion}
          chatBlockReason={chatBlockReason}
          onAskQuestion={askQuestion}
          onClearChat={clearChatMessages}
        />
      }
    />
  );
  const reportView = (
    <DailyReportPage
      report={report}
      loadingReport={loadingReport}
      busyAction={busyAction}
      statusLabel={statusLabel}
      manualUrl={manualUrl}
      onManualUrlChange={setManualUrl}
      onSubmitManual={() => void submitPrimaryAction()}
      onOpenSettings={() => openSettings("analysis")}
      onOpenItem={openNote}
      onDeleteFailedItem={(itemId) => void removeFailedReportItem(itemId)}
      onRunWechat={() => void runAction("wechat", () => ingestWechat(false))}
      onRunWechatFullScan={() => void runAction("wechat-full", () => ingestWechat(true))}
      onRunClipboard={() => void runAction("clipboard", ingestClipboard)}
      onRunDaily={() => void runAction("daily-run", () => runDailyNow(true, settingsDraft?.clipboard_include_on_schedule))}
      dailyRunBlockReason={dailyRunBlockReason}
      wechatBlockReason={wechatBlockReason}
      clipboardBlockReason={clipboardBlockReason}
      dailyStatus={dailyStatus}
      wechatScanDays={effectiveWechatScanDays}
      formatTimestamp={formatTimestamp}
    />
  );

  const settingsMenuView = (
    <SettingMenu
      items={settingsSections.map((item) => ({ id: item.id, title: item.title, subtitle: item.subtitle }))}
      activeId={activeSettingsSection}
      onSelect={(id) => openSettings(id as SettingsSection)}
    />
  );

  const settingsSaveAction = (
    <button className="bn-primary-button" type="button" disabled={!settingsDraft || busyAction === "save-settings"} onClick={() => void saveAllSettings()}>
      {busyAction === "save-settings" ? "保存中..." : "保存修改"}
    </button>
  );

  const settingsContentView = activeSettingsSection === "analysis" ? (
    <AnalysisSettingsPage
      settingsDraft={settingsDraft}
      noteFormatOptions={bootstrap?.note_formats ?? []}
      noteStyleOptions={bootstrap?.note_styles ?? []}
      analysisTargetOptions={analysisTargets.map((target) => ({ label: target.label, value: target.id }))}
      selectedAnalysisTargetId={draftAnalysisTargetId}
      onSelectAnalysisTarget={onSelectAnalysisTarget}
      onUpdateSettingsDraft={updateSettingsDraft}
      saveAction={settingsSaveAction}
    />
  ) : activeSettingsSection === "model" ? (
    <ModelSettingsPage
      busyAction={busyAction}
      createMode={isCreatingProvider}
      onStartCreateProvider={openNewProviderForm}
      onCreateProvider={(event) => void onCreateProvider(event)}
      newProviderDraft={newProviderDraft}
      onChangeNewProviderDraft={(patch) => setNewProviderDraft((current) => ({ ...current, ...patch }))}
      providerMenuItems={providerMenuItems.map(({ key, provider }) => ({
        key,
        provider,
        brand: getProviderBrand(provider),
        isActive: provider.provider_id === activeProviderId
      }))}
      onSelectProviderMenuItem={selectProviderMenuItem}
      activeProvider={activeProvider}
      activeProviderBrand={activeProviderBrand}
      onUpdateProviderEditor={(providerId, patch) => updateProviderEditor(providerId, patch)}
      onSaveProvider={(providerId) => void onSaveProvider(providerId)}
      onTestProvider={(providerId) => void onTestProvider(providerId)}
      onLoadProviderModels={(providerId) => void onLoadProviderModels(providerId)}
      onAddProviderModel={(providerId) => void onAddProviderModel(providerId)}
      onDeleteProviderModel={(modelId, providerId) => void onDeleteProviderModel(modelId, providerId)}
      activeProviderModels={activeProviderModels}
    />
  ) : activeSettingsSection === "transcriber" ? (
    <TranscriberPage
      settingsDraft={settingsDraft}
      providerEditors={providerEditors.map((provider) => ({ provider_id: provider.provider_id, label: provider.label }))}
      onUpdateSettingsDraft={updateSettingsDraft}
      saveAction={settingsSaveAction}
    />
  ) : activeSettingsSection === "download" ? (
    <DownloaderPage
      settingsDraft={settingsDraft}
      wechatAccounts={bootstrap?.wechat.accounts ?? []}
      autostartEnabled={Boolean(bootstrap?.schedule.autostart_enabled)}
      onUpdateSettingsDraft={updateSettingsDraft}
      saveAction={settingsSaveAction}
    />
  ) : (
    <MonitorPage health={health} dailyStatus={dailyStatus} formatTimestamp={formatTimestamp} getHealthFollowup={getHealthFollowup} />
  );
  const homeView = isNoteView ? noteDetailView : reportView;

  const settingsView = <SettingLayout menu={settingsMenuView} content={settingsContentView} onBackHome={openHome} />;

  return (
    <main className="bn-shell">
      {errorText ? (
        <div className="bn-error-banner" role="alert">
          <p>{errorText}</p>
          <button className="bn-banner-close" type="button" onClick={() => setErrorText("")} aria-label="关闭提示">
            关闭
          </button>
        </div>
      ) : null}
      {showSetupBanner ? (
        <div className={errorText ? "bn-setup-banner bn-setup-banner-offset" : "bn-setup-banner"} role="status">
          <div className="bn-banner-copy">
            {selectedTargetSetupHints.map((hint) => (
              <p key={hint}>{hint}</p>
            ))}
          </div>
          <button
            className="bn-banner-close"
            type="button"
            onClick={() => setDismissedSetupHintsSignature(setupHintsSignature)}
            aria-label="关闭提示"
          >
            关闭
          </button>
        </div>
      ) : null}
      <Suspense fallback={<PageFallback />}>
        {isSettingsView ? settingsView : homeView}
      </Suspense>
    </main>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <LinknoteShell />
    </BrowserRouter>
  );
}



