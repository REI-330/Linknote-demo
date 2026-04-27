import { useMemo } from "react";
import { Link, useLocation } from "react-router-dom";
import { ArrowLeft, BrainCircuit, Waves, Wrench } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSettingsStore } from "@/stores/settings-store";
import { useProviderStore } from "@/stores/provider-store";
import { AnalysisSection } from "./settings/analysis-section";
import { ModelSection } from "./settings/model-section";
import { TranscriberSection } from "./settings/transcriber-section";
import { DownloaderSection } from "./settings/downloader-section";
import { MonitorSection } from "./settings/monitor-section";

const sections = [
  { id: "analysis", title: "分析设置", subtitle: "笔记风格、输出格式与展示能力" },
  { id: "model", title: "AI 模型设置", subtitle: "提供商、模型与 API Key" },
  { id: "transcriber", title: "音频转写配置", subtitle: "转写方式与模型" },
  { id: "download", title: "采集与调度", subtitle: "来源抓取、Cookies 与定时任务" },
  { id: "monitor", title: "运行监控", subtitle: "健康检查与最近运行状态" },
];

export function SettingsPage() {
  const location = useLocation();
  const bootstrap = useSettingsStore((state) => state.bootstrap);
  const providers = useProviderStore((state) => state.providers);

  const sectionId = useMemo(() => {
    const match = location.pathname.match(/\/settings\/(.+)/);
    return match ? match[1].split("/")[0] : "analysis";
  }, [location.pathname]);

  const activeSection = sections.find((section) => section.id === sectionId) ?? sections[0];
  const analysisProvider = providers.find((provider) => provider.provider_id === bootstrap?.analysis.provider_id);

  return (
    <div className="mx-auto flex w-full max-w-[1220px] flex-1 flex-col gap-6 px-5 py-6 md:px-10 md:py-10">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <Link to="/" className="ln-action-button mb-4 inline-flex">
            <ArrowLeft className="h-4 w-4" />
            返回工作台
          </Link>
          <div className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-primary/80">
            Settings Center
          </div>
          <h1 className="ln-section-title">AI 模型与工作流配置</h1>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-muted-foreground md:text-base">
            根据 Stitch 设计稿重构后的设置中心，用于管理分析引擎、转写、采集与运行状态。
          </p>
        </div>
      </div>

      <section className="ln-panel flex flex-col gap-4 px-6 py-5 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-border/50 bg-primary/10 text-primary">
            <BrainCircuit className="h-6 w-6" />
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              当前主力分析引擎
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-lg font-semibold text-foreground">
              <span>{bootstrap?.analysis.model_name || "尚未选择模型"}</span>
              {analysisProvider ? (
                <span className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">
                  {analysisProvider.label}
                </span>
              ) : null}
            </div>
          </div>
        </div>
        <Link to="/settings/model" className="ln-action-button self-start md:self-auto">
          管理默认路由
        </Link>
      </section>

      <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
        <aside className="ln-glass h-fit rounded-[1.4rem] p-3">
          <nav className="space-y-1.5">
            {sections.map((section) => (
              <Link
                key={section.id}
                to={`/settings/${section.id}`}
                className={cn(
                  "block rounded-[1.15rem] px-4 py-3 transition-colors",
                  section.id === activeSection.id
                    ? "bg-primary/12 text-primary"
                    : "text-muted-foreground hover:bg-white/70 hover:text-foreground dark:hover:bg-slate-950/50"
                )}
              >
                <div className="text-sm font-semibold">{section.title}</div>
                <div className="mt-1 text-xs leading-5 opacity-80">{section.subtitle}</div>
              </Link>
            ))}
          </nav>
          <div className="mt-5 rounded-[1.15rem] border border-border/55 bg-card/72 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-foreground">
              <Waves className="h-4 w-4 text-primary" />
              采集节奏
            </div>
            <p className="text-xs leading-6 text-muted-foreground">
              当前定时整理时间为 {bootstrap?.schedule.daily_time || "--"}，微信与剪贴板采集可以在这里联动调整。
            </p>
          </div>
        </aside>

        <section className="min-w-0">
          {activeSection.id === "analysis" && <AnalysisSection />}
          {activeSection.id === "model" && <ModelSection />}
          {activeSection.id === "transcriber" && <TranscriberSection />}
          {activeSection.id === "download" && <DownloaderSection />}
          {activeSection.id === "monitor" && <MonitorSection />}
        </section>
      </div>
    </div>
  );
}
