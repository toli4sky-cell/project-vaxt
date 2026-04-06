import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { MainLayout } from "@/app/layout/MainLayout";
import { useAuth } from "@/app/providers/AuthProvider";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { TimesheetGridPage } from "@/pages/TimesheetGridPage";
import { EmployeesPage } from "@/pages/EmployeesPage";
import { TemplatesPage } from "@/pages/TemplatesPage";
import { VacationsPage } from "@/pages/VacationsPage";
import { HolidaysPage } from "@/pages/HolidaysPage";
import { CodesPage } from "@/pages/CodesPage";
import { AuditPage } from "@/pages/AuditPage";
import { ExportsPage } from "@/pages/ExportsPage";
import { SchedulePage } from "@/pages/SchedulePage";

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-400">Загрузка…</div>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <Protected>
            <MainLayout />
          </Protected>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/timesheet" element={<TimesheetGridPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
        <Route path="/templates" element={<TemplatesPage />} />
        <Route path="/vacations" element={<VacationsPage />} />
        <Route path="/holidays" element={<HolidaysPage />} />
        <Route path="/codes" element={<CodesPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/exports" element={<ExportsPage />} />
        <Route path="/schedule" element={<SchedulePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
