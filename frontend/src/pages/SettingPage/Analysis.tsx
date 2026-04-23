import { SettingsSectionFrame, ToggleField } from "../../app/FormPieces";
import type { SettingsUpdatePayload } from "../../types";

type Option = {
  label: string;
  value: string;
};

interface AnalysisSettingsPageProps {
  settingsDraft: SettingsUpdatePayload | null;
  noteFormatOptions: Option[];
  noteStyleOptions: Option[];
  analysisTargetOptions: Option[];
  selectedAnalysisTargetId: string;
  onSelectAnalysisTarget: (value: string) => void;
  onUpdateSettingsDraft: (patch: Partial<SettingsUpdatePayload>) => void;
  saveAction: React.ReactNode;
}

export default function AnalysisSettingsPage({
  settingsDraft,
  noteFormatOptions,
  noteStyleOptions,
  analysisTargetOptions,
  selectedAnalysisTargetId,
  onSelectAnalysisTarget,
  onUpdateSettingsDraft,
  saveAction
}: AnalysisSettingsPageProps) {
  const primaryFormatOptions = noteFormatOptions.filter((item) => item.value !== "link" && item.value !== "screenshot");
  const formatOptions = primaryFormatOptions.length ? primaryFormatOptions : noteFormatOptions;

  return (
    <SettingsSectionFrame title="分析设置" subtitle="把日报生成和单条重试共用的分析规则统一收进全局设置" action={saveAction}>
      {settingsDraft ? (
        <div className="bn-analysis-settings-grid">
          <section className="bn-settings-card">
            <div className="bn-settings-card-head">
              <h3>分析模型</h3>
              <span className="bn-pill neutral">设置页唯一来源</span>
            </div>
            <div className="bn-settings-form-grid">
              <label className="bn-field">
                <span>当前 provider / model</span>
                <select
                  value={selectedAnalysisTargetId}
                  onChange={(event) => onSelectAnalysisTarget(event.target.value)}
                  disabled={!analysisTargetOptions.length}
                >
                  {analysisTargetOptions.length ? null : <option value="">请先到 AI 模型设置启用模型</option>}
                  {analysisTargetOptions.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="bn-about-copy">
              <p>这里选中的 provider 和 model，就是日报整理、单条分析、失败重试、AI 问答统一使用的模型。</p>
              <p>系统不再按启用列表顺序自动挑选，也不再把“第一个可用模型”当成默认值。</p>
            </div>
          </section>

          <section className="bn-settings-card">
            <div className="bn-settings-card-head">
              <h3>输出偏好</h3>
              <span className="bn-pill neutral">全局生效</span>
            </div>
            <div className="bn-settings-form-grid">
              <label className="bn-field">
                <span>主输出格式</span>
                <select value={settingsDraft.note_format} onChange={(event) => onUpdateSettingsDraft({ note_format: event.target.value })}>
                  {formatOptions.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="bn-field">
                <span>笔记风格</span>
                <select value={settingsDraft.note_style} onChange={(event) => onUpdateSettingsDraft({ note_style: event.target.value })}>
                  {noteStyleOptions.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </section>

          <section className="bn-settings-card">
            <div className="bn-settings-card-head">
              <h3>展示增强</h3>
              <span className="bn-pill neutral">结果展示</span>
            </div>
            <div className="bn-check-grid">
              <ToggleField label="原片跳转" checked={settingsDraft.enable_source_links} onChange={(checked) => onUpdateSettingsDraft({ enable_source_links: checked })} />
              <ToggleField label="原片截图" checked={settingsDraft.enable_screenshots} onChange={(checked) => onUpdateSettingsDraft({ enable_screenshots: checked })} />
              <ToggleField label="AI 问答" checked={settingsDraft.enable_ai_chat} onChange={(checked) => onUpdateSettingsDraft({ enable_ai_chat: checked })} />
              <ToggleField label="思维导图" checked={settingsDraft.enable_mind_map} onChange={(checked) => onUpdateSettingsDraft({ enable_mind_map: checked })} />
            </div>
          </section>

          <section className="bn-settings-card">
            <div className="bn-about-copy">
              <p>这里控制的是后续自动整理和手动重生成时的统一分析偏好，不再放在单条笔记页左侧。</p>
              <p>单条详细页继续使用 LinkNote 的展示与交互；日报主页只保留预览和入口。</p>
            </div>
          </section>
        </div>
      ) : null}
    </SettingsSectionFrame>
  );
}
