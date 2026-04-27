import { Link, useLocation } from "react-router-dom";
import {
  BookText,
  BrainCircuit,
  ChevronRight,
  LayoutDashboard,
  PanelLeftClose,
  Settings2,
  Sparkles,
  Waves,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ModeToggle } from "@/components/mode-toggle";
import { useUiStore } from "@/stores/ui-store";

const navItems = [
  { to: "/", label: "Workspace", icon: LayoutDashboard },
  { to: "/settings/analysis", label: "Analysis", icon: BookText },
  { to: "/settings/model", label: "AI Models", icon: BrainCircuit },
  { to: "/settings/transcriber", label: "Transcription", icon: Waves },
  { to: "/settings/download", label: "Settings", icon: Settings2 },
];

export function AppSidebar() {
  const location = useLocation();
  const desktopSidebarCollapsed = useUiStore((state) => state.desktopSidebarCollapsed);
  const toggleDesktopSidebar = useUiStore((state) => state.toggleDesktopSidebar);

  return (
    <aside
      className={cn(
        "ln-glass fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-white/40 px-4 py-5 transition-transform duration-300 md:flex",
        desktopSidebarCollapsed && "-translate-x-[calc(100%-4.5rem)]"
      )}
    >
      <div className="mb-6 flex items-start justify-between gap-3 px-3 py-2">
        <Link
          to="/"
          className={cn(
            "flex min-w-0 items-center gap-3 rounded-2xl transition-colors hover:bg-white/60 dark:hover:bg-slate-900/55",
            desktopSidebarCollapsed ? "px-0 py-0" : "-mx-2 px-2 py-2"
          )}
        >
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-white/50 bg-primary/12 text-primary">
            <Sparkles className="h-5 w-5" />
          </div>
          <div
            className={cn(
              "min-w-0 transition-all duration-200",
              desktopSidebarCollapsed && "pointer-events-none w-0 overflow-hidden opacity-0"
            )}
          >
            <div className="font-['Spline_Sans'] text-xl font-extrabold tracking-tight text-primary">LinkNote</div>
            <p className="text-xs font-medium text-muted-foreground">知识编织中枢</p>
          </div>
        </Link>
        <button type="button" className="ln-icon-button hidden md:inline-flex" onClick={toggleDesktopSidebar} aria-label="切换侧边栏">
          <PanelLeftClose className={cn("h-4.5 w-4.5 transition-transform", desktopSidebarCollapsed && "rotate-180")} />
        </button>
      </div>

      <nav className="flex flex-1 flex-col gap-1.5 px-2">
        {navItems.map((item) => {
          const active = item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to);

          return (
            <Link
              key={item.to}
              to={item.to}
              title={desktopSidebarCollapsed ? item.label : undefined}
              className={cn(
                "group flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition-all duration-200",
                desktopSidebarCollapsed && "justify-center px-3",
                active
                  ? "bg-primary/12 text-primary shadow-[inset_0_0_0_1px_hsl(var(--primary)/0.12)]"
                  : "text-muted-foreground hover:bg-white/70 hover:text-foreground dark:hover:bg-slate-900/65"
              )}
            >
              <item.icon className={cn("h-4.5 w-4.5 shrink-0", active && "text-primary")} />
              <span
                className={cn(
                  "flex-1 whitespace-nowrap transition-all duration-200",
                  desktopSidebarCollapsed && "w-0 overflow-hidden opacity-0"
                )}
              >
                {item.label}
              </span>
              <ChevronRight
                className={cn(
                  "h-4 w-4 opacity-0 transition-all group-hover:translate-x-0.5 group-hover:opacity-100",
                  desktopSidebarCollapsed && "hidden",
                  active && "opacity-100"
                )}
              />
            </Link>
          );
        })}
      </nav>

      <div className="mt-6 border-t border-border/55 px-3 pt-4">
        <div className={cn("mb-4 flex items-center gap-3", desktopSidebarCollapsed && "justify-center")}>
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <span className="text-sm font-bold">U</span>
          </div>
          <div
            className={cn(
              "min-w-0 transition-all duration-200",
              desktopSidebarCollapsed && "w-0 overflow-hidden opacity-0"
            )}
          >
            <div className="truncate text-sm font-semibold text-foreground">Personal Studio</div>
            <div className="truncate text-xs text-muted-foreground">Flow State</div>
          </div>
        </div>
        <div className={cn("flex items-center justify-between", desktopSidebarCollapsed && "justify-center")}>
          <span
            className={cn(
              "text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground",
              desktopSidebarCollapsed && "hidden"
            )}
          >
            Theme
          </span>
          <ModeToggle />
        </div>
      </div>
    </aside>
  );
}
