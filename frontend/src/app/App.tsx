import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./Layout";
import { DailyReportPage } from "@/pages/DailyReportPage";
import { NotePage } from "@/pages/NotePage";
import { SettingsPage } from "@/pages/SettingsPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<DailyReportPage />} />
          <Route path="/notes/:itemId" element={<NotePage />} />
          <Route path="/settings/*" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
