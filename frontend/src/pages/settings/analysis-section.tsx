import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSettingsStore } from "@/stores/settings-store";
import { useProviderStore } from "@/stores/provider-store";
import { useMemo } from "react";

export function AnalysisSection() {
  const bootstrap = useSettingsStore((s) => s.bootstrap);
  const draft = useSettingsStore((s) => s.draft);
  const updateDraft = useSettingsStore((s) => s.updateDraft);
  const providers = useProviderStore((s) => s.providers);
  const enabledModels = useProviderStore((s) => s.enabledModels);

  const analysisTargets = useMemo(() => {
    return enabledModels.map((model) => {
      const provider = providers.find(
        (p) => p.provider_id === model.provider_id
      );
      return {
        id: `${model.provider_id}:${model.model_name}`,
        label: `${provider?.label ?? model.provider_id} / ${model.model_name}`,
        provider_id: model.provider_id,
        model_name: model.model_name,
      };
    });
  }, [enabledModels, providers]);

  const selectedTargetId = useMemo(() => {
    if (!draft?.analysis_provider_id || !draft.analysis_model_name) {
      return "";
    }
    const nextId = `${draft.analysis_provider_id}:${draft.analysis_model_name}`;
    return analysisTargets.some((item) => item.id === nextId) ? nextId : "";
  }, [analysisTargets, draft?.analysis_model_name, draft?.analysis_provider_id]);

  if (!draft || !bootstrap) {
    return (
      <Card className="border-dashed shadow-sm">
        <CardContent className="py-12 text-center text-muted-foreground font-medium">
          加载中...
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-5">
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">分析模型</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-semibold">当前模型</label>
            <Select
              value={selectedTargetId}
              onValueChange={(value) => {
                const target = analysisTargets.find((t) => t.id === value);
                if (target) {
                  updateDraft({
                    analysis_provider_id: target.provider_id,
                    analysis_model_name: target.model_name,
                  });
                }
              }}
              disabled={!analysisTargets.length}
            >
              <SelectTrigger className="h-10">
                <SelectValue
                  placeholder={
                    analysisTargets.length
                      ? "请选择模型"
                      : "请先到 AI 模型设置启用模型"
                  }
                />
              </SelectTrigger>
              <SelectContent>
                {analysisTargets.map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">输出偏好</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="space-y-2">
              <label className="text-sm font-semibold">主输出格式</label>
              <Select
                value={draft.note_format}
                onValueChange={(v) => updateDraft({ note_format: v })}
              >
                <SelectTrigger className="h-10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {bootstrap.note_formats.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold">笔记风格</label>
              <Select
                value={draft.note_style}
                onValueChange={(v) => updateDraft({ note_style: v })}
              >
                <SelectTrigger className="h-10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {bootstrap.note_styles.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">展示增强</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              {
                label: "原片跳转",
                checked: draft.enable_source_links,
                onChange: (v: boolean) =>
                  updateDraft({ enable_source_links: v }),
              },
              {
                label: "原片截图",
                checked: draft.enable_screenshots,
                onChange: (v: boolean) =>
                  updateDraft({ enable_screenshots: v }),
              },
              {
                label: "AI 问答",
                checked: draft.enable_ai_chat,
                onChange: (v: boolean) =>
                  updateDraft({ enable_ai_chat: v }),
              },
              {
                label: "思维导图",
                checked: draft.enable_mind_map,
                onChange: (v: boolean) =>
                  updateDraft({ enable_mind_map: v }),
              },
            ].map((field) => (
              <label
                key={field.label}
                className="flex items-center justify-between p-3.5 rounded-lg border bg-card/50 hover:bg-accent/40 transition-colors"
              >
                <span className="text-sm font-semibold">{field.label}</span>
                <Switch
                  checked={field.checked}
                  onCheckedChange={field.onChange}
                />
              </label>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
