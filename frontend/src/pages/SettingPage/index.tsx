import { Outlet } from "react-router-dom";

import { SettingLayout } from "../../layouts/SettingLayout";

interface SettingPageProps {
  menu: React.ReactNode;
  onBackHome: () => void;
}

export default function SettingPage({ menu, onBackHome }: SettingPageProps) {
  return <SettingLayout menu={menu} content={<Outlet />} onBackHome={onBackHome} />;
}
