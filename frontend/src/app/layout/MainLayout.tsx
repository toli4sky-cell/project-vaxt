import { NavLink, Outlet } from "react-router-dom";
import { cn } from "@/shared/lib/cn";
import { useAuth } from "@/app/providers/AuthProvider";
import { Button } from "@/shared/ui/Button";

const nav = [
  { to: "/", label: "Dashboard" },
  { to: "/timesheet", label: "Timesheet Grid" },
  { to: "/schedule", label: "Schedule Grid" },
  { to: "/schedule-excel", label: "Schedule Excel" },
  { to: "/schedule-excel-v2", label: "Schedule Excel v2" },
  { to: "/employees", label: "Employees" },
  { to: "/templates", label: "Templates" },
  { to: "/vacations", label: "Vacations" },
  { to: "/holidays", label: "Holidays" },
  { to: "/codes", label: "Codes" },
  { to: "/audit", label: "Audit" },
  { to: "/exports", label: "Exports" },
] as const;

export function MainLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 flex-col border-r border-slate-800 bg-slate-900/80">
        <div className="border-b border-slate-800 px-4 py-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Табель Т-12</div>
          <div className="mt-1 text-sm font-medium text-slate-100">Внутренняя система</div>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 p-2">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "rounded-md px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-100",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-800 p-3">
          <div className="truncate text-xs text-slate-500">{user?.email}</div>
          <Button variant="ghost" className="mt-2 w-full" onClick={() => logout()}>
            Выйти
          </Button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto bg-slate-950 p-8">
        <Outlet />
      </main>
    </div>
  );
}
