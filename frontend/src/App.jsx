import React from "react";
import { Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import NewScreening from "./pages/NewScreening";
import ScreeningHistory from "./pages/ScreeningHistory";
import ScreeningDetails from "./pages/ScreeningDetails";
import Reports from "./pages/Reports";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/screening/new" element={<NewScreening />} />
        <Route path="/history" element={<ScreeningHistory />} />
        <Route path="/screening/:caseId" element={<ScreeningDetails />} />
        <Route path="/reports/:caseId" element={<Reports />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppLayout>
  );
}
