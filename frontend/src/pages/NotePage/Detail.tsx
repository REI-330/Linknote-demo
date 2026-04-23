import { ArrowLeft, ArrowUpRight, Settings2 } from "lucide-react";
import type { ReactNode } from "react";

import logo from "../../assets/linknote-icon.svg";
import "../HomePage/workspace.css";

interface NoteDetailPageProps {
  preview: ReactNode;
  sourceUrl?: string;
  onBackHome: () => void;
  onOpenSettings: () => void;
}

export function NoteDetailPage({ preview, sourceUrl, onBackHome, onOpenSettings }: NoteDetailPageProps) {
  return (
    <div className="ln-note-page">
      <header className="ln-note-page-head">
        <div className="ln-note-page-brand">
          <div className="ln-note-page-brand-logo">
            <img src={logo} alt="LinkNote" />
          </div>
          <div className="ln-note-page-brand-copy">
            <strong>单条笔记</strong>
            <p>这里专门看单条分析结果，生成参数和个性化偏好统一放到设置页。</p>
          </div>
        </div>

        <div className="ln-note-page-actions">
          <button className="bn-ghost-button" type="button" onClick={onBackHome}>
            <ArrowLeft size={16} />
            返回日报
          </button>
          {sourceUrl ? (
            <button
              className="bn-ghost-button"
              type="button"
              onClick={() => window.open(sourceUrl, "_blank", "noopener,noreferrer")}
            >
              打开原片
              <ArrowUpRight size={15} />
            </button>
          ) : null}
          <button className="bn-secondary-button" type="button" onClick={onOpenSettings}>
            <Settings2 size={16} />
            设置
          </button>
        </div>
      </header>

      <main className="ln-note-page-body">{preview}</main>
    </div>
  );
}
