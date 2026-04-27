import { create } from "zustand";
import {
  analyzeNote,
  askNoteQuestion,
  getNoteDetail,
  reanalyzeNote,
} from "@/api";
import type { NoteChatSource, NoteDetail } from "@/types";

export type ChatPanelMode = false | "half" | "full";

export type ChatMessage = {
  role: "assistant" | "user";
  content: string;
  sources?: NoteChatSource[];
};

interface NoteState {
  detail: NoteDetail | null;
  loading: boolean;
  selectedVersionId: string;
  chatMessages: ChatMessage[];
  chatQuestion: string;
  chatPanelMode: ChatPanelMode;
  showSourceReference: boolean;
  busyAction: string;
  error: string | null;

  refreshNote: (itemId: string, reportDate?: string) => Promise<void>;
  analyze: (itemId: string, reportDate?: string) => Promise<void>;
  reanalyze: (itemId: string, reportDate?: string) => Promise<void>;
  askQuestion: (itemId: string, reportDate?: string) => Promise<void>;
  setChatQuestion: (value: string) => void;
  clearChat: () => void;
  setSelectedVersionId: (id: string) => void;
  setChatPanelMode: (mode: ChatPanelMode) => void;
  toggleChatPanel: () => void;
  setShowSourceReference: (show: boolean) => void;
  toggleSourceReference: () => void;
  resetNote: () => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

const assistantGreeting =
  "这里会基于当前笔记、原文片段和视频信息继续回答问题。";

export const useNoteStore = create<NoteState>((set, get) => ({
  detail: null,
  loading: false,
  selectedVersionId: "",
  chatMessages: [{ role: "assistant", content: assistantGreeting }],
  chatQuestion: "",
  chatPanelMode: false,
  showSourceReference: false,
  busyAction: "",
  error: null,

  refreshNote: async (itemId, reportDate) => {
    set({ loading: true, error: null });
    try {
      const detail = await getNoteDetail(itemId, reportDate);
      set({ detail });
      // Auto-select first version
      const firstVersion = detail.analysis.versions[0];
      if (firstVersion) {
        set({ selectedVersionId: firstVersion.version_id });
      }
      // Initialize UI state from backend
      set({
        showSourceReference: Boolean(detail.analysis.panels?.source_reference),
        chatPanelMode: detail.analysis.panels?.ai_chat ? "half" : false,
      });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ loading: false });
    }
  },

  analyze: async (itemId, reportDate) => {
    set({ busyAction: "analyze", error: null });
    try {
      await analyzeNote(itemId, reportDate);
      await get().refreshNote(itemId, reportDate);
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ busyAction: "" });
    }
  },

  reanalyze: async (itemId, reportDate) => {
    set({ busyAction: "reanalyze", error: null });
    try {
      await reanalyzeNote(itemId, reportDate);
      await get().refreshNote(itemId, reportDate);
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ busyAction: "" });
    }
  },

  askQuestion: async (itemId, reportDate) => {
    const { chatQuestion, chatMessages } = get();
    if (!chatQuestion.trim()) return;

    const question = chatQuestion.trim();
    set({
      chatMessages: [...chatMessages, { role: "user", content: question }],
      chatQuestion: "",
      busyAction: "chat",
      error: null,
    });

    try {
      const history = get()
        .chatMessages.filter((m) => m.role === "assistant" || m.role === "user")
        .map((m) => ({ role: m.role, content: m.content }));
      const response = await askNoteQuestion(
        itemId,
        question,
        history,
        undefined,
        reportDate
      );
      set((state) => ({
        chatMessages: [
          ...state.chatMessages,
          {
            role: "assistant",
            content: response.answer,
            sources: response.sources ?? [],
          },
        ],
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      set((state) => ({
        error: message,
        chatMessages: [
          ...state.chatMessages,
          { role: "assistant", content: `问答失败：${message}` },
        ],
      }));
    } finally {
      set({ busyAction: "" });
    }
  },

  setChatQuestion: (value) => set({ chatQuestion: value }),

  clearChat: () =>
    set({
      chatMessages: [{ role: "assistant", content: assistantGreeting }],
    }),

  setSelectedVersionId: (id) => set({ selectedVersionId: id }),

  setChatPanelMode: (mode) => set({ chatPanelMode: mode }),

  toggleChatPanel: () =>
    set((state) => ({
      chatPanelMode: state.chatPanelMode ? false : "half",
    })),

  setShowSourceReference: (show) => set({ showSourceReference: show }),

  toggleSourceReference: () =>
    set((state) => ({
      showSourceReference: !state.showSourceReference,
    })),

  resetNote: () =>
    set({
      detail: null,
      loading: false,
      selectedVersionId: "",
      chatMessages: [{ role: "assistant", content: assistantGreeting }],
      chatQuestion: "",
      chatPanelMode: false,
      showSourceReference: false,
      busyAction: "",
    }),

  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));
