import type { ScheduleViewMode } from "@/pages/schedule/scheduleGridConfig";
import { Button } from "@/shared/ui/Button";

const MONTH_OPTIONS: { value: number; label: string }[] = [
  { value: 1, label: "Январь" },
  { value: 2, label: "Февраль" },
  { value: 3, label: "Март" },
  { value: 4, label: "Апрель" },
  { value: 5, label: "Май" },
  { value: 6, label: "Июнь" },
  { value: 7, label: "Июль" },
  { value: 8, label: "Август" },
  { value: 9, label: "Сентябрь" },
  { value: 10, label: "Октябрь" },
  { value: 11, label: "Ноябрь" },
  { value: 12, label: "Декабрь" },
];

type ScheduleGridToolbarProps = {
  viewMode: ScheduleViewMode;
  onViewModeChange: (mode: ScheduleViewMode) => void;
  month: number;
  onMonthChange: (month: number) => void;
  year: number;
  employeeCount: number;
  loading: boolean;
  onRefresh: () => void;
};

export function ScheduleGridToolbar({
  viewMode,
  onViewModeChange,
  month,
  onMonthChange,
  year,
  employeeCount,
  loading,
  onRefresh,
}: ScheduleGridToolbarProps) {
  const monthLabel = MONTH_OPTIONS[month - 1]?.label ?? "";

  return (
    <div className="flex flex-col gap-3 border-b border-slate-200/90 bg-white px-3 py-2.5 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
      <div className="min-w-0 flex-1">
        <h1 className="truncate text-base font-semibold text-slate-900">График работы / табель Т-12</h1>
        <p className="mt-0.5 text-xs text-slate-600">
          <span className="text-slate-800">{year}</span>
          {" · "}
          {viewMode === "year" ? "просмотр: год" : `просмотр: ${monthLabel}`}
          {" · "}
          <span className="font-medium text-slate-800">{employeeCount}</span> сотр.
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex rounded-md border border-slate-200 bg-slate-50 p-0.5 shadow-sm">
          <button
            type="button"
            className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
              viewMode === "year" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
            }`}
            onClick={() => onViewModeChange("year")}
          >
            Год
          </button>
          <button
            type="button"
            className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
              viewMode === "month" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
            }`}
            onClick={() => onViewModeChange("month")}
          >
            Месяц
          </button>
        </div>
        {viewMode === "month" ? (
          <select
            className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-900 shadow-sm outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-200"
            value={month}
            onChange={(e) => onMonthChange(Number(e.target.value))}
          >
            {MONTH_OPTIONS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        ) : null}
        <Button className="py-1.5 text-xs" variant="primary" disabled={loading} onClick={() => onRefresh()}>
          {loading ? "Загрузка…" : "Обновить"}
        </Button>
      </div>
    </div>
  );
}
