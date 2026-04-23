import { SlidersHorizontal } from "lucide-react";
import { ReactNode } from "react";

import logo from "../assets/linknote-icon.svg";

interface SettingLayoutProps {
  menu: ReactNode;
  content: ReactNode;
  onBackHome: () => void;
}

export function SettingLayout({ menu, content, onBackHome }: SettingLayoutProps) {
  return (
    <div className="bn-settings-layout-shell">
      <aside className="bn-settings-layout-menu">
        <header className="bn-settings-layout-head">
          <div className="bn-layout-brand-copy brand">
            <div className="bn-layout-brand-logo">
              <img src={logo} alt="LinkNote" />
            </div>
            <strong>LinkNote</strong>
          </div>
          <div className="bn-layout-brand-actions">
            <button className="bn-layout-icon" type="button" onClick={onBackHome}>
              <SlidersHorizontal size={18} />
            </button>
          </div>
        </header>
        <div className="bn-layout-scroll">{menu}</div>
      </aside>
      <main className="bn-settings-layout-content">{content}</main>
    </div>
  );
}
