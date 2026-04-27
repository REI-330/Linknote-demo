import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSettingsStore } from "@/stores/settings-store";
import { useProviderStore } from "@/stores/provider-store";

export function TranscriberSection() {
  const draft = useSettingsStore((s) => s.draft);
  const updateDraft = useSettingsStore((s) => s.updateDraft);
  const providers = useProviderStore((s) => s.providers);

  const isOpenAICompatible = draft?.transcriber_type === "openai_compatible";
  const selectedProviderId =
    draft && providers.some((provider) => provider.provider_id === draft.transcriber_provider_id)
      ? draft.transcriber_provider_id
      : "";

  if (!draft) {
    return (
      <Card className="border-dashed shadow-sm">
        <CardContent className="py-12 text-center text-muted-foreground font-medium">
          加载中...
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">音频转写配置</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="space-y-2">
            <label className="text-sm font-semibold">转写类型</label>
            <Select
              value={draft.transcriber_type}
              onValueChange={(v) => updateDraft({ transcriber_type: v })}
            >
              <SelectTrigger className="h-10">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="faster_whisper">
                  faster_whisper（本地）
                </SelectItem>
                <SelectItem value="openai_compatible">
                  openai_compatible（云端）
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold">转写提供商</label>
            <Select
              value={selectedProviderId}
              onValueChange={(v) =>
                updateDraft({ transcriber_provider_id: v })
              }
              disabled={!isOpenAICompatible}
            >
              <SelectTrigger className="h-10">
                <SelectValue placeholder="请选择 provider" />
              </SelectTrigger>
              <SelectContent>
                {providers.map((provider) => (
                  <SelectItem
                    key={provider.provider_id}
                    value={provider.provider_id}
                  >
                    {provider.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold">转写模型</label>
            <Input
              value={draft.transcriber_model_name}
              placeholder={isOpenAICompatible ? "whisper-1" : "small"}
              onChange={(e) =>
                updateDraft({ transcriber_model_name: e.target.value })
              }
              className="h-10"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold">转写语言</label>
            <Input
              value={draft.transcriber_language}
              onChange={(e) =>
                updateDraft({ transcriber_language: e.target.value })
              }
              className="h-10"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
