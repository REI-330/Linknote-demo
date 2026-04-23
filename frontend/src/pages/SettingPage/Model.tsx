import type { FormEvent } from "react";

import { ProviderLogo } from "../../app/ProviderLogo";
import type { EnabledModelRecord, RemoteModelRecord } from "../../types";

type ProviderDraft = {
  name: string;
  base_url: string;
  api_key: string;
};

type ProviderBrand = {
  label: string;
  icon: string;
};

export type ProviderEditorView = {
  provider_id: string;
  label: string;
  logo: string;
  type: string;
  enabled: boolean;
  base_url: string;
  api_key: string;
  api_key_env: string;
  remoteModels: RemoteModelRecord[];
  remoteModelName: string;
  manualModelName: string;
  isLoadingModels: boolean;
  isSaving: boolean;
  isTesting: boolean;
  isAddingModel: boolean;
};

export type ProviderMenuItemView = {
  key: string;
  provider: ProviderEditorView;
  brand: ProviderBrand;
  isActive: boolean;
};

interface ModelSettingsPageProps {
  busyAction: string;
  createMode: boolean;
  onStartCreateProvider: () => void;
  onCreateProvider: (event: FormEvent<HTMLFormElement>) => void;
  newProviderDraft: ProviderDraft;
  onChangeNewProviderDraft: (patch: Partial<ProviderDraft>) => void;
  providerMenuItems: ProviderMenuItemView[];
  onSelectProviderMenuItem: (provider: ProviderEditorView) => void;
  activeProvider: ProviderEditorView | null;
  activeProviderBrand: ProviderBrand | null;
  onUpdateProviderEditor: (providerId: string, patch: Partial<ProviderEditorView>) => void;
  onSaveProvider: (providerId: string) => void;
  onTestProvider: (providerId: string) => void;
  onLoadProviderModels: (providerId: string) => void;
  onAddProviderModel: (providerId: string) => void;
  onDeleteProviderModel: (modelId: string, providerId: string) => void;
  activeProviderModels: EnabledModelRecord[];
}

type ProviderFormPanelProps = {
  provider: ProviderEditorView;
  brand: ProviderBrand;
  onUpdateProviderEditor: (providerId: string, patch: Partial<ProviderEditorView>) => void;
  onSaveProvider: (providerId: string) => void;
  onTestProvider: (providerId: string) => void;
  onLoadProviderModels: (providerId: string) => void;
  onAddProviderModel: (providerId: string) => void;
  onDeleteProviderModel: (modelId: string, providerId: string) => void;
  activeProviderModels: EnabledModelRecord[];
};

function ProviderEditorPanel({
  provider,
  brand,
  onUpdateProviderEditor,
  onSaveProvider,
  onTestProvider,
  onLoadProviderModels,
  onAddProviderModel,
  onDeleteProviderModel,
  activeProviderModels
}: ProviderFormPanelProps) {
  return (
    <>
      <div className="bn-provider-editor-head">
        <div className="bn-provider-editor-title">
          <div className="bn-provider-logo large">
            <ProviderLogo name={brand.icon} size={28} />
          </div>
          <div>
            <h3>编辑模型提供商</h3>
            <p>{brand.label}</p>
          </div>
        </div>
      </div>

      <div className="bn-provider-editor-form">
        <label className="bn-field">
          <span>名称</span>
          <input
            value={provider.label}
            disabled={provider.type === "built-in"}
            onChange={(event) => onUpdateProviderEditor(provider.provider_id, { label: event.target.value })}
          />
        </label>
        <label className="bn-field">
          <span>API Key</span>
          <input
            value={provider.api_key}
            onChange={(event) => onUpdateProviderEditor(provider.provider_id, { api_key: event.target.value })}
            placeholder={provider.api_key_env ? `环境变量回退：${provider.api_key_env}` : ""}
          />
        </label>
        <label className="bn-field wide">
          <span>API 地址</span>
          <div className="bn-inline-input-action">
            <input value={provider.base_url} onChange={(event) => onUpdateProviderEditor(provider.provider_id, { base_url: event.target.value })} />
            <button className="bn-inline-text-action" type="button" disabled={provider.isTesting} onClick={() => onTestProvider(provider.provider_id)}>
              {provider.isTesting ? "测试中..." : "测试连通性"}
            </button>
          </div>
        </label>
        <label className="bn-field">
          <span>类型</span>
          <input value={provider.type} readOnly />
        </label>
      </div>

      <div className="bn-provider-editor-actions">
        <button className="bn-secondary-button compact" type="button" disabled={provider.isSaving} onClick={() => onSaveProvider(provider.provider_id)}>
          {provider.isSaving ? "保存中..." : "保存修改"}
        </button>
      </div>

      <div className="bn-model-editor-panel">
        <div className="bn-model-editor-head stacked">
          <h4>模型列表</h4>
          <div className="bn-inline-warning">请确认已经保存提供商信息，并且通过测试连通性。</div>
        </div>

        <div className="bn-field-group">
          <div className="bn-inline-label-row">
            <span>选择模型</span>
            <button className="bn-inline-text-action" type="button" disabled={provider.isLoadingModels} onClick={() => onLoadProviderModels(provider.provider_id)}>
              {provider.isLoadingModels ? "加载中..." : "刷新模型"}
            </button>
          </div>
          <select value={provider.remoteModelName} onChange={(event) => onUpdateProviderEditor(provider.provider_id, { remoteModelName: event.target.value })}>
            <option value="">{provider.isLoadingModels ? "加载中..." : "请选择模型"}</option>
            {provider.remoteModels.map((model) => (
              <option key={model.id} value={model.id}>
                {model.id}
              </option>
            ))}
          </select>
        </div>

        <div className="bn-field-group">
          <span className="bn-field-label">手动输入模型</span>
          <input
            value={provider.manualModelName}
            placeholder="gpt-4.1-mini"
            onChange={(event) => onUpdateProviderEditor(provider.provider_id, { manualModelName: event.target.value })}
          />
        </div>

        <button className="bn-primary-button wide" type="button" disabled={provider.isAddingModel} onClick={() => onAddProviderModel(provider.provider_id)}>
          {provider.isAddingModel ? "保存中..." : "保存模型"}
        </button>

        <div className="bn-enabled-models">
          <strong>已启用模型</strong>
          <div className="bn-chip-list">
            {activeProviderModels.length ? (
              activeProviderModels.map((model) => (
                <span key={model.id} className="bn-chip">
                  {model.model_name}
                  <button type="button" onClick={() => onDeleteProviderModel(model.id, provider.provider_id)}>
                    ×
                  </button>
                </span>
              ))
            ) : (
              <p className="bn-muted-copy">当前 provider 还没有启用模型。</p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default function ModelSettingsPage({
  busyAction,
  createMode,
  onStartCreateProvider,
  onCreateProvider,
  newProviderDraft,
  onChangeNewProviderDraft,
  providerMenuItems,
  onSelectProviderMenuItem,
  activeProvider,
  activeProviderBrand,
  onUpdateProviderEditor,
  onSaveProvider,
  onTestProvider,
  onLoadProviderModels,
  onAddProviderModel,
  onDeleteProviderModel,
  activeProviderModels
}: ModelSettingsPageProps) {
  return (
    <div className="bn-model-settings-screen">
      <div className="bn-model-settings-layout">
        <section className="bn-provider-list-column">
          <div className="bn-provider-list-head">
            <button className="bn-primary-button" type="button" onClick={onStartCreateProvider}>
              添加模型提供商
            </button>
            <span>模型提供商列表</span>
          </div>

          <div className="bn-provider-list">
            {providerMenuItems.length ? (
              providerMenuItems.map((item) => (
                <button
                  key={item.key}
                  className={item.isActive ? "bn-provider-card active" : "bn-provider-card"}
                  type="button"
                  onClick={() => onSelectProviderMenuItem(item.provider)}
                >
                  <div className="bn-provider-card-main">
                    <div className="bn-provider-logo">
                      <ProviderLogo name={item.brand.icon} size={24} />
                    </div>
                    <strong>{item.brand.label}</strong>
                  </div>
                  <label className="bn-inline-switch" onClick={(event) => event.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={item.provider.enabled}
                      onChange={(event) => onUpdateProviderEditor(item.provider.provider_id, { enabled: event.target.checked })}
                    />
                    <span />
                  </label>
                </button>
              ))
            ) : (
              <p className="bn-muted-copy">还没有 provider，先新增一个。</p>
            )}
          </div>
        </section>

        <section className="bn-provider-editor-card">
          {createMode ? (
            <form className="bn-provider-create-pane" onSubmit={onCreateProvider}>
              <div className="bn-provider-editor-head">
                <div className="bn-provider-editor-title">
                  <div>
                    <h3>新增模型提供商</h3>
                    <p>直接按 LinkNote 的右侧表单流新增，不再把创建流程塞进左栏。</p>
                  </div>
                </div>
              </div>

              <div className="bn-provider-create">
                <label className="bn-field">
                  <span>名称</span>
                  <input value={newProviderDraft.name} onChange={(event) => onChangeNewProviderDraft({ name: event.target.value })} />
                </label>
                <label className="bn-field">
                  <span>API 地址</span>
                  <input value={newProviderDraft.base_url} onChange={(event) => onChangeNewProviderDraft({ base_url: event.target.value })} />
                </label>
                <label className="bn-field">
                  <span>API Key</span>
                  <input value={newProviderDraft.api_key} onChange={(event) => onChangeNewProviderDraft({ api_key: event.target.value })} />
                </label>
              </div>

              <div className="bn-provider-editor-actions">
                <button className="bn-secondary-button compact" type="submit" disabled={busyAction === "create-provider"}>
                  {busyAction === "create-provider" ? "创建中..." : "保存提供商"}
                </button>
              </div>
            </form>
          ) : activeProvider && activeProviderBrand ? (
            <ProviderEditorPanel
              provider={activeProvider}
              brand={activeProviderBrand}
              onUpdateProviderEditor={onUpdateProviderEditor}
              onSaveProvider={onSaveProvider}
              onTestProvider={onTestProvider}
              onLoadProviderModels={onLoadProviderModels}
              onAddProviderModel={onAddProviderModel}
              onDeleteProviderModel={onDeleteProviderModel}
              activeProviderModels={activeProviderModels}
            />
          ) : (
            <div className="bn-empty-box">
              <strong>先从左侧选择一个 provider</strong>
              <p>如果还没有模型提供商，点击“添加模型提供商”进入新增页。</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
