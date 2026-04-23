import { Activity, BotMessageSquare, Captions, HardDriveDownload, Info, SlidersHorizontal } from "lucide-react";

export type SettingMenuItem = {
  id: string;
  title: string;
  subtitle: string;
};

interface SettingMenuProps {
  items: SettingMenuItem[];
  activeId: string;
  onSelect: (id: string) => void;
}

const iconMap = {
  analysis: SlidersHorizontal,
  model: BotMessageSquare,
  transcriber: Captions,
  download: HardDriveDownload,
  monitor: Activity
} as const;

export function SettingMenu({ items, activeId, onSelect }: SettingMenuProps) {
  return (
    <div className="bn-settings-menu-copy">
      <div className="bn-settings-menu-title">
        <h1>设置</h1>
        <p>全局配置与模型设置</p>
      </div>
      <nav className="bn-settings-nav" aria-label="设置菜单">
        {items.map((item) => {
          const Icon = iconMap[item.id as keyof typeof iconMap] ?? Info;
          return (
            <button
              key={item.id}
              className={item.id === activeId ? "bn-settings-nav-item active" : "bn-settings-nav-item"}
              type="button"
              onClick={() => onSelect(item.id)}
            >
              <Icon size={18} />
              <strong>{item.title}</strong>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
