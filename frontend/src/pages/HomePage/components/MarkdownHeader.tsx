import { BrainCircuit, Copy, Download, FileText, MessageSquare } from "lucide-react";

type WorkspaceMode = "markdown" | "mindmap";
type ChatPanelMode = false | "half" | "full";

type VersionRecord = {
  version_id: string;
  model_name: string;
  created_at: string;
};

interface MarkdownHeaderProps {
  versions: VersionRecord[];
  selectedVersionId: string;
  onSelectVersion: (id: string) => void;
  modelName?: string;
  providerSummary: string;
  styleLabel: string;
  createdAt?: string;
  copied: boolean;
  onCopy: () => void;
  onDownload: () => void;
  showSourceReference: boolean;
  onToggleSourceReference: () => void;
  chatPanelMode: ChatPanelMode;
  onToggleChatPanel: () => void;
  aiChatEnabled: boolean;
  workspaceMode: WorkspaceMode;
  onToggleWorkspaceMode: () => void;
  formatTimestamp: (value?: string) => string;
}

export function MarkdownHeader({
  versions,
  selectedVersionId,
  onSelectVersion,
  modelName,
  providerSummary,
  styleLabel,
  createdAt,
  copied,
  onCopy,
  onDownload,
  showSourceReference,
  onToggleSourceReference,
  chatPanelMode,
  onToggleChatPanel,
  aiChatEnabled,
  workspaceMode,
  onToggleWorkspaceMode,
  formatTimestamp
}: MarkdownHeaderProps) {
  return (
    <header className="ln-preview-toolbar">
      <div className="ln-preview-toolbar-main">
        {versions.length > 1 ? (
          <div className="ln-version-picker">
            <select value={selectedVersionId} onChange={(event) => onSelectVersion(event.target.value)}>
              {versions.map((version) => (
                <option key={version.version_id} value={version.version_id}>
                  {`版本 ${version.version_id.slice(-6)}`}
                </option>
              ))}
            </select>
          </div>
        ) : null}
        {modelName ? <span className="bn-pill hot">{modelName}</span> : null}
        <span className="bn-pill neutral">{providerSummary}</span>
        <span className="bn-pill neutral">{styleLabel}</span>
        {createdAt ? <span className="ln-toolbar-meta">创建时间: {formatTimestamp(createdAt)}</span> : null}
      </div>

      <div className="ln-preview-toolbar-actions">
        <button className={workspaceMode === "mindmap" ? "bn-ghost-button active" : "bn-ghost-button"} type="button" onClick={onToggleWorkspaceMode}>
          <BrainCircuit size={16} />
          <span>{workspaceMode === "markdown" ? "思维导图" : "Markdown"}</span>
        </button>
        <button className="bn-ghost-button" type="button" onClick={onCopy}>
          <Copy size={16} />
          <span>{copied ? "已复制" : "复制"}</span>
        </button>
        <button className="bn-ghost-button" type="button" onClick={onDownload}>
          <Download size={16} />
          <span>导出 Markdown</span>
        </button>
        <button className={showSourceReference ? "bn-ghost-button active" : "bn-ghost-button"} type="button" onClick={onToggleSourceReference}>
          <FileText size={16} />
          <span>原文参照</span>
        </button>
        <button
          className={chatPanelMode ? "bn-ghost-button active" : "bn-ghost-button"}
          type="button"
          onClick={onToggleChatPanel}
          disabled={!aiChatEnabled}
        >
          <MessageSquare size={16} />
          <span>AI 问答</span>
        </button>
      </div>
    </header>
  );
}
