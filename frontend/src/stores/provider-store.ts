import { create } from "zustand";
import {
  addEnabledModel,
  addProvider,
  deleteEnabledModel,
  fetchEnabledModels,
  fetchEnabledModelsByProvider,
  fetchProviderModels,
  getProviderList,
  testProviderConnection,
  updateProvider,
} from "@/api";
import type {
  EnabledModelRecord,
  ProviderRecord,
  RemoteModelRecord,
} from "@/types";

export type ProviderEditor = ProviderRecord & {
  remoteModels: RemoteModelRecord[];
  remoteModelName: string;
  manualModelName: string;
  isLoadingModels: boolean;
  isSaving: boolean;
  isTesting: boolean;
  isAddingModel: boolean;
};

function mergeProviderEditors(
  records: ProviderRecord[],
  current: ProviderEditor[]
): ProviderEditor[] {
  return records.map((record) => {
    const previous = current.find(
      (item) => item.provider_id === record.provider_id
    );
    return {
      ...record,
      remoteModels: previous?.remoteModels ?? [],
      remoteModelName: previous?.remoteModelName ?? "",
      manualModelName: previous?.manualModelName ?? "",
      isLoadingModels: false,
      isSaving: false,
      isTesting: false,
      isAddingModel: false,
    };
  });
}

function normalizeModelNameList(modelNames: string[]) {
  const normalized: string[] = [];
  for (const modelName of modelNames) {
    const cleanName = modelName.trim();
    if (cleanName && !normalized.includes(cleanName)) {
      normalized.push(cleanName);
    }
  }
  return normalized;
}

function addModelToProviderState<
  T extends { default_model: string; models: string[] }
>(provider: T, modelName: string): T {
  const cleanName = modelName.trim();
  if (!cleanName) return provider;
  return {
    ...provider,
    default_model: provider.default_model.trim() || cleanName,
    models: normalizeModelNameList([...provider.models, cleanName]),
  };
}

function removeModelFromProviderState<
  T extends { default_model: string; models: string[] }
>(provider: T, modelName: string): T {
  const cleanName = modelName.trim();
  if (!cleanName) return provider;
  const nextModels = normalizeModelNameList(
    provider.models.filter((name) => name.trim() !== cleanName)
  );
  const nextDefaultModel =
    provider.default_model.trim() === cleanName
      ? (nextModels[0] ?? "")
      : provider.default_model;
  return {
    ...provider,
    default_model: nextDefaultModel,
    models: nextModels,
  };
}

interface ProviderState {
  providers: ProviderEditor[];
  enabledModels: EnabledModelRecord[];
  loading: boolean;
  error: string | null;

  refreshProviders: () => Promise<void>;
  updateProviderField: (
    providerId: string,
    patch: Partial<ProviderEditor>
  ) => void;
  saveProvider: (providerId: string) => Promise<void>;
  testProvider: (providerId: string) => Promise<void>;
  loadProviderModels: (providerId: string) => Promise<void>;
  addProviderModel: (providerId: string) => Promise<void>;
  deleteProviderModel: (modelId: string, providerId: string) => Promise<void>;
  createProvider: (payload: {
    name: string;
    base_url: string;
    api_key: string;
  }) => Promise<string>;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useProviderStore = create<ProviderState>((set, get) => ({
  providers: [],
  enabledModels: [],
  loading: false,
  error: null,

  refreshProviders: async () => {
    set({ loading: true });
    try {
      const [nextProviders, nextModels] = await Promise.all([
        getProviderList(),
        fetchEnabledModels(),
      ]);
      set((state) => ({
        providers: mergeProviderEditors(nextProviders, state.providers),
        enabledModels: nextModels,
      }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      set({ loading: false });
    }
  },

  updateProviderField: (providerId, patch) => {
    set((state) => ({
      providers: state.providers.map((provider) =>
        provider.provider_id === providerId
          ? { ...provider, ...patch }
          : provider
      ),
    }));
  },

  saveProvider: async (providerId) => {
    const provider = get().providers.find(
      (p) => p.provider_id === providerId
    );
    if (!provider) return;

    get().updateProviderField(providerId, { isSaving: true });
    set({ error: null });

    try {
      await updateProvider({
        id: provider.provider_id,
        name: provider.label.trim(),
        api_key: provider.api_key.trim(),
        base_url: provider.base_url.trim(),
        enabled: provider.enabled ? 1 : 0,
      });
      await get().refreshProviders();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      get().updateProviderField(providerId, { isSaving: false });
    }
  },

  testProvider: async (providerId) => {
    const provider = get().providers.find(
      (p) => p.provider_id === providerId
    );
    if (!provider) return;

    get().updateProviderField(providerId, { isTesting: true });
    set({ error: null });

    try {
      await updateProvider({
        id: provider.provider_id,
        name: provider.label.trim(),
        api_key: provider.api_key.trim(),
        base_url: provider.base_url.trim(),
        enabled: provider.enabled ? 1 : 0,
      });
      await testProviderConnection(providerId);
      await get().refreshProviders();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      get().updateProviderField(providerId, { isTesting: false });
    }
  },

  loadProviderModels: async (providerId) => {
    const provider = get().providers.find(
      (p) => p.provider_id === providerId
    );
    if (!provider) return;

    get().updateProviderField(providerId, { isLoadingModels: true });
    set({ error: null });

    try {
      await updateProvider({
        id: provider.provider_id,
        name: provider.label.trim(),
        api_key: provider.api_key.trim(),
        base_url: provider.base_url.trim(),
        enabled: provider.enabled ? 1 : 0,
      });
      const [response, providerEnabledModels] = await Promise.all([
        fetchProviderModels(providerId),
        fetchEnabledModelsByProvider(providerId),
      ]);
      const enabledNames = new Set(
        providerEnabledModels.map((item) => item.model_name.trim())
      );
      const availableModels = response.models.filter(
        (model) => !enabledNames.has(model.id.trim())
      );
      get().updateProviderField(providerId, {
        isLoadingModels: false,
        remoteModels: availableModels,
        remoteModelName: availableModels[0]?.id ?? "",
      });
      await get().refreshProviders();
    } catch (err) {
      get().updateProviderField(providerId, { isLoadingModels: false });
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    }
  },

  addProviderModel: async (providerId) => {
    const provider = get().providers.find(
      (p) => p.provider_id === providerId
    );
    if (!provider) return;

    const modelName = (provider.manualModelName || provider.remoteModelName).trim();
    if (!modelName) {
      set({ error: "先选择远端模型，或手动填写模型名。" });
      return;
    }

    const enabledNames = new Set(
      get()
        .enabledModels.filter((item) => item.provider_id === providerId)
        .map((item) => item.model_name.trim())
    );
    if (enabledNames.has(modelName)) {
      set({
        error: "这个模型已经在当前提供商里启用了，不需要重复保存。",
      });
      return;
    }

    get().updateProviderField(providerId, { isAddingModel: true });
    set({ error: null });

    try {
      const response = await addEnabledModel(providerId, modelName);
      const model = response.model;

      set((state) => ({
        enabledModels: [...state.enabledModels, model],
        providers: state.providers.map((p) =>
          p.provider_id === providerId
            ? addModelToProviderState(
                { ...p, remoteModelName: "", manualModelName: "" },
                model.model_name
              )
            : p
        ),
      }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      get().updateProviderField(providerId, { isAddingModel: false });
    }
  },

  deleteProviderModel: async (modelId, providerId) => {
    get().updateProviderField(providerId, { isAddingModel: true });
    set({ error: null });

    try {
      await deleteEnabledModel(modelId);
      const separatorIndex = modelId.indexOf(":");
      const modelName =
        separatorIndex >= 0 ? modelId.slice(separatorIndex + 1) : "";

      set((state) => ({
        enabledModels: state.enabledModels.filter((item) => item.id !== modelId),
        providers: state.providers.map((p) =>
          p.provider_id === providerId
            ? removeModelFromProviderState(p, modelName)
            : p
        ),
      }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      get().updateProviderField(providerId, { isAddingModel: false });
    }
  },

  createProvider: async (payload) => {
    set({ busyAction: "create-provider", error: null } as Partial<ProviderState> & { busyAction?: string });
    try {
      const response = await addProvider({
        name: payload.name.trim(),
        api_key: payload.api_key.trim(),
        base_url: payload.base_url.trim(),
        type: "custom",
      });
      await get().refreshProviders();
      return response.id;
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Unknown error" });
      throw err;
    } finally {
      set({ busyAction: "" } as Partial<ProviderState> & { busyAction?: string });
    }
  },

  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));
