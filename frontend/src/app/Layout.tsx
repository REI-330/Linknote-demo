import { useEffect, useMemo } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { Bell, BrainCircuit, LayoutDashboard, PanelLeftOpen, Settings2, Waves } from "lucide-react";
import { AppSidebar } from "@/components/app-sidebar";
import { ModeToggle } from "@/components/mode-toggle";
import { useThemeStore } from "@/stores/theme-store";
import { useReportStore } from "@/stores/report-store";
import { useSettingsStore } from "@/stores/settings-store";
import { useProviderStore } from "@/stores/provider-store";
import { useNoteStore } from "@/stores/note-store";
import { useUiStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";

const mobileNavItems = [
  { to: "/", label: "Home", icon: LayoutDashboard },
  { to: "/settings/analysis", label: "Analysis", icon: BrainCircuit },
  { to: "/settings/transcriber", label: "Capture", icon: Waves },
  { to: "/settings/download", label: "Settings", icon: Settings2 },
];

export function Layout() {
  const location = useLocation();
  const initTheme = useThemeStore((state) => state.init);
  const refreshReport = useReportStore((state) => state.refreshReport);
  const refreshAll = useSettingsStore((state) => state.refreshAll);
  const refreshProviders = useProviderStore((state) => state.refreshProviders);
  const report = useReportStore((state) => state.report);
  const busyAction = useReportStore((state) => state.busyAction);

  const reportError = useReportStore((state) => state.error);
  const settingsError = useSettingsStore((state) => state.error);
  const providerError = useProviderStore((state) => state.error);
  const noteError = useNoteStore((state) => state.error);
  const clearReportError = useReportStore((state) => state.clearError);
  const clearSettingsError = useSettingsStore((state) => state.clearError);
  const clearProviderError = useProviderStore((state) => state.clearError);
  const clearNoteError = useNoteStore((state) => state.clearError);
  const desktopSidebarCollapsed = useUiStore((state) => state.desktopSidebarCollapsed);
  const toggleDesktopSidebar = useUiStore((state) => state.toggleDesktopSidebar);

  useEffect(() => {
    initTheme();
  }, [initTheme]);

  useEffect(() => {
    refreshReport();
    refreshAll();
    refreshProviders();
  }, [refreshReport, refreshAll, refreshProviders]);

  const hasBackgroundWork =
    busyAction === "daily-run" ||
    report?.items.some((item) => item.status === "pending" || item.status === "running");

  useEffect(() => {
    if (!hasBackgroundWork) {
      return;
    }

    const timer = window.setInterval(() => {
      refreshReport().catch(() => undefined);
    }, 4000);

    return () => window.clearInterval(timer);
  }, [hasBackgroundWork, refreshReport]);

  const topError = useMemo(
    () => reportError || settingsError || providerError || noteError || "",
    [noteError, providerError, reportError, settingsError]
  );

  function clearTopError() {
    clearReportError();
    clearSettingsError();
    clearProviderError();
    clearNoteError();
  }

  return (
    <div className="ln-page-shell">
      <AppSidebar />

      <div
        className={cn(
          "flex min-h-screen flex-1 flex-col transition-[padding] duration-300",
          desktopSidebarCollapsed ? "md:pl-[4.5rem]" : "md:pl-64"
        )}
      >
        <button
          type="button"
          onClick={toggleDesktopSidebar}
          className={cn(
            "ln-icon-button fixed left-4 top-4 z-30 hidden md:inline-flex",
            desktopSidebarCollapsed ? "opacity-100" : "pointer-events-none opacity-0"
          )}
          aria-label="展开侧边栏"
        >
          <PanelLeftOpen className="h-4.5 w-4.5" />
        </button>

        <header className="ln-glass sticky top-0 z-30 flex h-16 items-center justify-between border-b border-white/45 px-5 md:hidden">
          <Link to="/" className="font-['Spline_Sans'] text-lg font-extrabold tracking-tight text-primary">
            LinkNote
          </Link>
          <div className="flex items-center gap-2">
            <button type="button" className="ln-icon-button">
              <Bell className="h-4.5 w-4.5" />
            </button>
            <ModeToggle />
          </div>
        </header>

        {topError ? (
          <div className="sticky top-16 z-20 px-4 pt-4 md:top-4 md:px-6">
            <div className="ln-panel mx-auto flex max-w-6xl items-start justify-between gap-4 border-destructive/25 bg-destructive/6 px-5 py-4 text-sm text-destructive">
              <p className="leading-6">{topError}</p>
              <button
                type="button"
                onClick={clearTopError}
                className="rounded-full px-3 py-1 text-xs font-semibold hover:bg-destructive/10"
              >
                关闭
              </button>
            </div>
          </div>
        ) : null}

        <main className="flex flex-1 flex-col pb-24 md:pb-0">
          <Outlet />
        </main>

        <nav className="ln-glass fixed inset-x-0 bottom-0 z-40 mx-3 mb-3 flex items-center justify-around rounded-[1.6rem] px-2 py-2 md:hidden">
          {mobileNavItems.map((item) => {
            const active =
              item.to === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(item.to);

            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "flex min-w-[72px] flex-col items-center gap-1 rounded-2xl px-3 py-2 text-[11px] font-semibold transition-colors",
                  active
                    ? "bg-primary/12 text-primary"
                    : "text-muted-foreground hover:bg-white/70 hover:text-foreground"
                )}
              >
                <item.icon className="h-4.5 w-4.5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
