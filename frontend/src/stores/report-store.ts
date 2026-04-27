import { create } from "zustand";
import {
  deleteFailedReportItem,
  getReportByDate,
  getTodayReport,
  ingestClipboard,
  ingestManual,
  ingestWechat,
  runDailyNow,
} from "@/api";
import type { ReportSummary } from "@/types";

interface ReportState {
  report: ReportSummary | null;
  loading: boolean;
  reportDate: string;
  busyAction: string;
  error: string | null;

  setReportDate: (date: string) => void;
  refreshReport: () => Promise<void>;
  setError: (error: string | null) => void;
  clearError: () => void;

  ingestWechat: (forceFullScan?: boolean) => Promise<void>;
  ingestClipboard: () => Promise<void>;
  ingestManual: (url: string) => Promise<void>;
  runDaily: (includeClipboard?: boolean) => Promise<void>;
  deleteFailedItem: (itemId: string) => Promise<void>;
}

export const useReportStore = create<ReportState>((set, get) => ({
  report: null,
  loading: false,
  reportDate: "",
  busyAction: "",
  error: null,

  setReportDate: (date) => set({ reportDate: date }),

  refreshReport: async () => {
    set({ loading: true, error: null });
    try {
      const { reportDate } = get();
      const next = reportDate
        ? await getReportByDate(reportDate)
        : await getTodayReport();
      set({ report: next, reportDate: next.report_date });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ loading: false });
    }
  },

  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),

  ingestWechat: async (forceFullScan = false) => {
    set({ busyAction: forceFullScan ? "wechat-full" : "wechat", error: null });
    try {
      await ingestWechat(forceFullScan);
      await get().refreshReport();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ busyAction: "" });
    }
  },

  ingestClipboard: async () => {
    set({ busyAction: "clipboard", error: null });
    try {
      await ingestClipboard();
      await get().refreshReport();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ busyAction: "" });
    }
  },

  ingestManual: async (url) => {
    set({ busyAction: "manual", error: null });
    try {
      await ingestManual(url, "manual-bilibili");
      await get().refreshReport();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ busyAction: "" });
    }
  },

  runDaily: async (includeClipboard) => {
    set({ busyAction: "daily-run", error: null });
    try {
      await runDailyNow(true, includeClipboard);
      await get().refreshReport();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ busyAction: "" });
    }
  },

  deleteFailedItem: async (itemId) => {
    const { report } = get();
    if (!report) return;
    set({ busyAction: `delete-failed:${itemId}`, error: null });
    try {
      await deleteFailedReportItem(report.report_date, itemId);
      await get().refreshReport();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ busyAction: "" });
    }
  },
}));
