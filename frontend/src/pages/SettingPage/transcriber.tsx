import { SettingsSectionFrame } from "../../app/FormPieces";
import type { SettingsUpdatePayload } from "../../types";

type ProviderOption = {
  provider_id: string;
  label: string;
};

interface TranscriberPageProps {
  settingsDraft: SettingsUpdatePayload | null;
  providerEditors: ProviderOption[];
  onUpdateSettingsDraft: (patch: Partial<SettingsUpdatePayload>) => void;
  saveAction: React.ReactNode;
}

export default function TranscriberPage({
  settingsDraft,
  providerEditors,
  onUpdateSettingsDraft,
  saveAction
}: TranscriberPageProps) {
  const isOpenAICompatible = settingsDraft?.transcriber_type === "openai_compatible";
  const modelPlaceholder = isOpenAICompatible ? "whisper-1" : "small";

  return (
    <SettingsSectionFrame title="音频转写配置" subtitle="转写方式、模型与提供商" action={saveAction}>
      {settingsDraft ? (
        <section className="bn-settings-card">
          <div className="bn-settings-form-grid">
            <label className="bn-field">
              <span>转写类型</span>
              <select value={settingsDraft.transcriber_type} onChange={(event) => onUpdateSettingsDraft({ transcriber_type: event.target.value })}>
                <option value="faster_whisper">faster_whisper（本地）</option>
                <option value="openai_compatible">openai_compatible（云端）</option>
              </select>
            </label>
            <label className="bn-field">
              <span>转写提供商</span>
              <select
                value={settingsDraft.transcriber_provider_id}
                disabled={!isOpenAICompatible}
                onChange={(event) => onUpdateSettingsDraft({ transcriber_provider_id: event.target.value })}
              >
                <option value="">请选择 provider</option>
                {providerEditors.map((provider) => (
                  <option key={provider.provider_id} value={provider.provider_id}>
                    {provider.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="bn-field">
              <span>转写模型</span>
              <input
                value={settingsDraft.transcriber_model_name}
                placeholder={modelPlaceholder}
                onChange={(event) => onUpdateSettingsDraft({ transcriber_model_name: event.target.value })}
              />
            </label>
            <label className="bn-field">
              <span>转写语言</span>
              <input value={settingsDraft.transcriber_language} onChange={(event) => onUpdateSettingsDraft({ transcriber_language: event.target.value })} />
            </label>
          </div>
        </section>
      ) : null}
    </SettingsSectionFrame>
  );
}
