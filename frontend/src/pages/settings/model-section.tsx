import { useState, useEffect, useMemo } from "react";
import {
  Plus,
  Trash2,
  RefreshCw,
  Save,
  Zap,
  AlertCircle,
  Loader2,
  Bot,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProviderStore } from "@/stores/provider-store";
import { cn } from "@/lib/utils";

const PROVIDER_LOGOS: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google",
  deepseek: "DeepSeek",
  siliconflow: "SiliconFlow",
  custom: "Custom",
};

function ProviderLogo({ logo, className }: { logo: string; className?: string }) {
  const label = PROVIDER_LOGOS[logo] ?? logo;
  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-md bg-muted text-xs font-semibold text-muted-foreground shrink-0",
        className
      )}
    >
      {label[0]?.toUpperCase() ?? "?"}
    </div>
  );
}

export function ModelSection() {
  const providers = useProviderStore((s) => s.providers);
  const enabledModels = useProviderStore((s) => s.enabledModels);
  const loading = useProviderStore((s) => s.loading);
  const error = useProviderStore((s) => s.error);
  const refreshProviders = useProviderStore((s) => s.refreshProviders);
  const updateProviderField = useProviderStore((s) => s.updateProviderField);
  const saveProvider = useProviderStore((s) => s.saveProvider);
  const testProvider = useProviderStore((s) => s.testProvider);
  const loadProviderModels = useProviderStore((s) => s.loadProviderModels);
  const addProviderModel = useProviderStore((s) => s.addProviderModel);
  const deleteProviderModel = useProviderStore((s) => s.deleteProviderModel);
  const createProvider = useProviderStore((s) => s.createProvider);
  const clearError = useProviderStore((s) => s.clearError);

  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [newProvider, setNewProvider] = useState({
    name: "",
    base_url: "",
    api_key: "",
  });

  useEffect(() => {
    refreshProviders();
  }, [refreshProviders]);

  // Auto-select first provider if none selected
  useEffect(() => {
    if (!selectedProviderId && providers.length > 0) {
      setSelectedProviderId(providers[0].provider_id);
    }
  }, [providers, selectedProviderId]);

  const selectedProvider = useMemo(
    () => providers.find((p) => p.provider_id === selectedProviderId) ?? null,
    [providers, selectedProviderId]
  );

  const selectedEnabledModels = useMemo(
    () =>
      enabledModels.filter(
        (m) => m.provider_id === selectedProviderId
      ),
    [enabledModels, selectedProviderId]
  );

  const handleCreateProvider = async () => {
    if (!newProvider.name.trim() || !newProvider.base_url.trim()) return;
    setCreating(true);
    clearError();
    try {
      const id = await createProvider({
        name: newProvider.name,
        base_url: newProvider.base_url,
        api_key: newProvider.api_key,
      });
      setNewProvider({ name: "", base_url: "", api_key: "" });
      setSelectedProviderId(id);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-5">
      {error && (
        <div className="flex items-start gap-2 p-3 rounded-lg border bg-destructive/5 border-destructive/20 text-destructive text-sm">
          <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
          <div className="flex-1">{error}</div>
          <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={clearError}>
            清除
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-5">
        {/* Provider list */}
        <div className="space-y-4">
          <Card className="shadow-sm">
            <CardHeader className="pb-2 pt-5 px-5">
              <CardTitle className="text-sm font-semibold">提供商列表</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1.5 px-5 pb-5">
              {loading && providers.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin mx-auto mb-2" />
                  加载中...
                </div>
              ) : (
                providers.map((provider) => (
                  <button
                    key={provider.provider_id}
                    onClick={() => setSelectedProviderId(provider.provider_id)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors",
                      selectedProviderId === provider.provider_id
                        ? "bg-primary/10 text-primary ring-1 ring-primary/20"
                        : "hover:bg-muted"
                    )}
                  >
                    <ProviderLogo logo={provider.logo} className="w-8 h-8" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold truncate">
                        {provider.label}
                      </div>
                      <div className="text-xs text-muted-foreground truncate font-medium">
                        {provider.provider_id}
                      </div>
                    </div>
                    <Switch
                      checked={provider.enabled}
                      onCheckedChange={(v) => {
                        updateProviderField(provider.provider_id, { enabled: v });
                        saveProvider(provider.provider_id);
                      }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </button>
                ))
              )}
            </CardContent>
          </Card>

          {/* Create new provider */}
          <Card className="shadow-sm">
            <CardHeader className="pb-2 pt-5 px-5">
              <CardTitle className="text-sm font-semibold">新建提供商</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2.5 px-5 pb-5">
              <Input
                placeholder="名称，如 My OpenRouter"
                value={newProvider.name}
                onChange={(e) =>
                  setNewProvider((p) => ({ ...p, name: e.target.value }))
                }
                className="h-10"
              />
              <Input
                placeholder="Base URL，如 https://api.openai.com/v1"
                value={newProvider.base_url}
                onChange={(e) =>
                  setNewProvider((p) => ({ ...p, base_url: e.target.value }))
                }
                className="h-10"
              />
              <Input
                type="password"
                placeholder="API Key（可选）"
                value={newProvider.api_key}
                onChange={(e) =>
                  setNewProvider((p) => ({ ...p, api_key: e.target.value }))
                }
                className="h-10"
              />
              <Button
                size="sm"
                className="w-full h-9"
                disabled={
                  creating ||
                  !newProvider.name.trim() ||
                  !newProvider.base_url.trim()
                }
                onClick={handleCreateProvider}
              >
                {creating ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Plus className="h-3.5 w-3.5 mr-1" />
                )}
                添加提供商
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Editor */}
        <div className="space-y-5">
          {selectedProvider ? (
            <>
              {/* Provider info */}
              <Card className="shadow-sm">
                <CardHeader className="pt-5 px-5 pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <ProviderLogo logo={selectedProvider.logo} className="w-10 h-10 text-sm" />
                      <div>
                        <CardTitle className="text-base font-semibold">{selectedProvider.label}</CardTitle>
                        <div className="flex items-center gap-2 mt-0.5">
                          <Badge variant={selectedProvider.enabled ? "success" : "secondary"} className="text-xs font-medium">
                            {selectedProvider.enabled ? "已启用" : "已禁用"}
                          </Badge>
                          <span className="text-xs text-muted-foreground font-mono">
                            {selectedProvider.provider_id}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={selectedProvider.isTesting}
                        onClick={() => testProvider(selectedProvider.provider_id)}
                        className="h-8"
                      >
                        {selectedProvider.isTesting ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                        ) : (
                          <Zap className="h-3.5 w-3.5 mr-1" />
                        )}
                        测试连接
                      </Button>
                      <Button
                        size="sm"
                        disabled={selectedProvider.isSaving}
                        onClick={() => saveProvider(selectedProvider.provider_id)}
                        className="h-8"
                      >
                        {selectedProvider.isSaving ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                        ) : (
                          <Save className="h-3.5 w-3.5 mr-1" />
                        )}
                        保存
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="px-5 pb-5 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div className="space-y-2">
                      <label className="text-sm font-semibold">显示名称</label>
                      <Input
                        value={selectedProvider.label}
                        onChange={(e) =>
                          updateProviderField(selectedProvider.provider_id, {
                            label: e.target.value,
                          })
                        }
                        className="h-10"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-semibold">Base URL</label>
                      <Input
                        value={selectedProvider.base_url}
                        placeholder="https://..."
                        onChange={(e) =>
                          updateProviderField(selectedProvider.provider_id, {
                            base_url: e.target.value,
                          })
                        }
                        className="h-10"
                      />
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <label className="text-sm font-semibold">API Key</label>
                      <div className="flex items-center gap-2">
                        <Input
                          type="password"
                          value={selectedProvider.api_key}
                          placeholder={
                            selectedProvider.api_key_env
                              ? `使用环境变量 ${selectedProvider.api_key_env}`
                              : "输入 API Key"
                          }
                          onChange={(e) =>
                            updateProviderField(selectedProvider.provider_id, {
                              api_key: e.target.value,
                            })
                          }
                          className="h-10"
                        />
                        {selectedProvider.api_key_env && (
                          <Badge variant="outline" className="shrink-0 text-xs font-medium">
                            ENV
                          </Badge>
                        )}
                      </div>
                      {selectedProvider.api_key_env && (
                        <p className="text-xs text-muted-foreground font-medium">
                          当前使用环境变量 {selectedProvider.api_key_env}，直接输入会覆盖。
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Models */}
              <Card className="shadow-sm">
                <CardHeader className="pt-5 px-5 pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-semibold">模型管理</CardTitle>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={selectedProvider.isLoadingModels}
                      onClick={() => loadProviderModels(selectedProvider.provider_id)}
                      className="h-8"
                    >
                      {selectedProvider.isLoadingModels ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                      ) : (
                        <RefreshCw className="h-3.5 w-3.5 mr-1" />
                      )}
                      加载远端模型
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="px-5 pb-5 space-y-4">
                  {/* Enabled models */}
                  {selectedEnabledModels.length > 0 && (
                    <div className="space-y-2">
                      <label className="text-sm font-semibold">已启用模型</label>
                      <div className="flex flex-wrap gap-2">
                        {selectedEnabledModels.map((model) => (
                          <Badge
                            key={model.id}
                            variant="secondary"
                            className="pl-2 pr-1 py-1 gap-1 text-xs font-medium"
                          >
                            <Bot className="h-3 w-3" />
                            {model.model_name}
                            <button
                              className="ml-0.5 rounded-sm hover:bg-muted-foreground/20 p-0.5"
                              onClick={() =>
                                deleteProviderModel(model.id, model.provider_id)
                              }
                              title="删除"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedProvider.models.length > 0 && (
                    <p className="text-xs text-muted-foreground font-medium">
                      默认模型：{selectedProvider.default_model || "未设置"}
                    </p>
                  )}

                  <Separator />

                  {/* Add model */}
                  <div className="space-y-3">
                    <label className="text-sm font-semibold">添加模型</label>
                    <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3">
                      {selectedProvider.remoteModels.length > 0 && (
                        <Select
                          value={selectedProvider.remoteModelName}
                          onValueChange={(v) =>
                            updateProviderField(selectedProvider.provider_id, {
                              remoteModelName: v,
                              manualModelName: "",
                            })
                          }
                        >
                          <SelectTrigger className="h-10">
                            <SelectValue placeholder="选择远端模型" />
                          </SelectTrigger>
                          <SelectContent>
                            {selectedProvider.remoteModels.map((model) => (
                              <SelectItem key={model.id} value={model.id}>
                                {model.id}
                                {model.owned_by && (
                                  <span className="text-muted-foreground ml-1">
                                    ({model.owned_by})
                                  </span>
                                )}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                      <Input
                        placeholder="或手动输入模型名"
                        value={selectedProvider.manualModelName}
                        onChange={(e) =>
                          updateProviderField(selectedProvider.provider_id, {
                            manualModelName: e.target.value,
                            remoteModelName: "",
                          })
                        }
                        className="h-10"
                      />
                      <Button
                        size="sm"
                        disabled={selectedProvider.isAddingModel}
                        onClick={() =>
                          addProviderModel(selectedProvider.provider_id)
                        }
                        className="h-10 md:h-9"
                      >
                        {selectedProvider.isAddingModel ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                        ) : (
                          <Plus className="h-3.5 w-3.5 mr-1" />
                        )}
                        添加
                      </Button>
                    </div>
                    {selectedProvider.remoteModels.length === 0 && (
                      <p className="text-xs text-muted-foreground font-medium">
                        没有可用的远端模型列表，直接输入模型名即可添加。
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="border-dashed shadow-sm">
              <CardContent className="py-16 text-center text-muted-foreground">
                <Bot className="h-8 w-8 mx-auto mb-3 opacity-50" />
                <p className="font-medium">请从左侧选择一个提供商，或新建一个。</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
