import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UiState {
  desktopSidebarCollapsed: boolean;
  setDesktopSidebarCollapsed: (collapsed: boolean) => void;
  toggleDesktopSidebar: () => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      desktopSidebarCollapsed: false,
      setDesktopSidebarCollapsed: (desktopSidebarCollapsed) => set({ desktopSidebarCollapsed }),
      toggleDesktopSidebar: () =>
        set((state) => ({ desktopSidebarCollapsed: !state.desktopSidebarCollapsed })),
    }),
    {
      name: "linknote-ui",
      partialize: (state) => ({ desktopSidebarCollapsed: state.desktopSidebarCollapsed }),
    }
  )
);
