export interface ReportItem {
  item_id: string;
  dedupe_key: string;
  source_url: string;
  source_title: string;
  source_context: string;
  source_origins: string[];
  collected_at: string;
  status: string;
  has_note: boolean;
  failure_code: string;
  failure_title: string;
  failure_hint: string;
  versions: number;
  detail_path: string;
}

export interface NoteChatSource {
  text: string;
  source_type: string;
  title?: string;
  section_title?: string;
  start_time?: number;
  end_time?: number;
  jump_url?: string;
}

export interface ProviderRecord {
  id: string;
  provider_id: string;
  name: string;
  label: string;
  logo: string;
  type: string;
  enabled: boolean;
  base_url: string;
  api_key: string;
  api_key_env: string;
  default_model: string;
  models: string[];
}

export interface EnabledModelRecord {
  id: string;
  provider_id: string;
  model_name: string;
}

export interface RemoteModelRecord {
  id: string;
  created: number;
  object: string;
  owned_by: string;
  permission: string;
  root: string;
}

export interface ReportSummary {
  report_date: string;
  total_items: number;
  pending_items: number;
  completed_items: number;
  failed_items: number;
  items: ReportItem[];
}

export interface NoteDetail {
  item: ReportItem;
  media: {
    platform: string;
    video_id: string;
    canonical_url: string;
    cover_url: string;
    duration: number;
    uploader: string;
    description: string;
    transcript_source: string;
    tags: string[];
  };
  analysis: {
    status: string;
    progress: {
      stage: string;
      step: string;
      detail: string;
      started_at: string;
      updated_at: string;
    };
    versions: Array<{
      version_id: string;
      label: string;
      markdown: string;
      source_basis: string;
      created_at: string;
      model_name: string;
      provider_id: string;
    }>;
    view_modes: string[];
    panels: {
      source_reference: boolean;
      ai_chat: boolean;
    };
    message: string;
    failure: {
      code: string;
      title: string;
      hint: string;
      actions: string[];
    };
    source_reference: Array<{
      start: number;
      end: number;
      text: string;
      speaker: string;
    }>;
  };
}

export interface SettingsBootstrap {
  note_formats: Array<{ label: string; value: string }>;
  note_styles: Array<{ label: string; value: string }>;
  providers: Array<{
    provider_id: string;
    label: string;
    logo: string;
    type: string;
    base_url: string;
    api_key: string;
    api_key_env: string;
    default_model: string;
    models: string[];
    enabled: boolean;
  }>;
  schedule: {
    enabled: boolean;
    daily_time: string;
    auto_collect_wechat: boolean;
    notify_on_complete: boolean;
    autostart_enabled: boolean;
  };
  analysis: {
    note_format: string;
    note_style: string;
    enable_source_links: boolean;
    enable_mind_map: boolean;
    enable_ai_chat: boolean;
    enable_screenshots: boolean;
    provider_id: string;
    model_name: string;
  };
  transcriber: {
    type: string;
    provider_id: string;
    model_name: string;
    language: string;
  };
  retention: {
    days: number;
    cleanup_intermediate: boolean;
  };
  server: {
    host: string;
    port: number;
    open_browser: boolean;
    lan_enabled: boolean;
  };
  wechat: {
    enabled: boolean;
    chatlog_root: string;
    account_dir: string;
    scan_days: number;
    accounts: Array<{
      account_dir: string;
      chatlog_root: string;
      label: string;
    }>;
  };
  clipboard: {
    enabled: boolean;
    include_on_schedule: boolean;
  };
  bilibili: {
    cookies_file: string;
    use_browser_cookies: boolean;
  };
  notification: {
    enabled: boolean;
    open_target: string;
  };
}

export interface SettingsUpdatePayload {
  wechat_enabled: boolean;
  wechat_chatlog_root: string;
  wechat_account_dir: string;
  wechat_scan_days: number;
  clipboard_enabled: boolean;
  bilibili_cookies_file: string;
  bilibili_use_browser_cookies: boolean;
  schedule_enabled: boolean;
  daily_time: string;
  auto_collect_wechat: boolean;
  notify_on_complete: boolean;
  clipboard_include_on_schedule: boolean;
  retention_days: number;
  cleanup_intermediate: boolean;
  note_format: string;
  note_style: string;
  enable_source_links: boolean;
  enable_mind_map: boolean;
  enable_ai_chat: boolean;
  enable_screenshots: boolean;
  analysis_provider_id: string;
  analysis_model_name: string;
  server_host: string;
  server_port: number;
  server_open_browser: boolean;
  lan_enabled: boolean;
  notification_enabled: boolean;
  notification_open_target: string;
  transcriber_type: string;
  transcriber_provider_id: string;
  transcriber_model_name: string;
  transcriber_language: string;
  providers: Array<{
    provider_id: string;
    label: string;
    logo: string;
    type: string;
    base_url: string;
    api_key: string;
    api_key_env: string;
    default_model: string;
    models: string[];
    enabled: boolean;
  }>;
}

export interface DailyRunStatus {
  schedule_enabled?: boolean;
  daily_time?: string;
  auto_collect_wechat?: boolean;
  include_clipboard?: boolean;
  notify_on_complete?: boolean;
  next_run_at?: string;
  is_running?: boolean;
  current_reason?: string;
  current_report_date?: string;
  current_started_at?: string;
  last_error?: string;
  last_reason?: string;
  last_report_date?: string;
  last_started_at?: string;
  last_finished_at?: string;
  last_run?: {
    report_date: string;
    collected_sources: string[];
    analyzed_item_ids: string[];
    failed_item_ids: string[];
    total_items: number;
    completed_items: number;
    failed_items: number;
    pending_items: number;
    started_at: string;
    finished_at: string;
  };
}

export interface HealthBootstrap {
  status: string;
  checks: Array<{
    key: string;
    label: string;
    status: string;
    detail: string;
    code?: string;
    followup?: string;
  }>;
}

export const EMPTY_REPORT_ITEM: ReportItem = {
  item_id: "",
  dedupe_key: "",
  source_url: "",
  source_title: "",
  source_context: "",
  source_origins: [],
  collected_at: "",
  status: "pending",
  has_note: false,
  failure_code: "",
  failure_title: "",
  failure_hint: "",
  versions: 0,
  detail_path: "",
};

export const EMPTY_NOTE_DETAIL: NoteDetail = {
  item: { ...EMPTY_REPORT_ITEM },
  media: {
    platform: "",
    video_id: "",
    canonical_url: "",
    cover_url: "",
    duration: 0,
    uploader: "",
    description: "",
    transcript_source: "",
    tags: [],
  },
  analysis: {
    status: "pending",
    progress: {
      stage: "",
      step: "",
      detail: "",
      started_at: "",
      updated_at: "",
    },
    versions: [],
    view_modes: ["markdown"],
    panels: {
      source_reference: false,
      ai_chat: false,
    },
    message: "",
    failure: {
      code: "",
      title: "",
      hint: "",
      actions: [],
    },
    source_reference: [],
  },
};
