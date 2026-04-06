import type { ColDef } from "ag-grid-community";
import { ScheduleDayCellRenderer, type ScheduleGridRow } from "@/pages/schedule/ScheduleDayCellRenderer";

export const SCHEDULE_DAYS_COUNT = 365;

function pad2(v: number): string {
  return String(v).padStart(2, "0");
}

export function getScheduleDates(year: number, daysCount: number = SCHEDULE_DAYS_COUNT): Date[] {
  const start = new Date(year, 0, 1);
  const dates: Date[] = [];
  for (let i = 0; i < daysCount; i++) {
    dates.push(new Date(start.getFullYear(), start.getMonth(), start.getDate() + i));
  }
  return dates;
}

function formatHeaderDate(date: Date): string {
  // День/месяц
  return `${pad2(date.getDate())}/${pad2(date.getMonth() + 1)}`;
}

function formatTooltipDate(date: Date): string {
  // Полная дата для tooltip
  return date.toISOString().slice(0, 10);
}

function EmployeeInfoCellRenderer(params: { data: ScheduleGridRow | undefined }) {
  const row = params.data;
  if (!row) return null;

  return (
    <div className="flex flex-col gap-1 px-2 py-1">
      <div className="truncate text-sm font-semibold text-white">{row.fio}</div>
      <div className="truncate text-xs text-slate-300">Таб. {row.tabNumber}</div>
      <div className="truncate text-xs text-slate-400">{row.department}</div>
    </div>
  );
}

export function getScheduleColumnDefs(year: number): ColDef<ScheduleGridRow>[] {
  const dates = getScheduleDates(year, SCHEDULE_DAYS_COUNT);

  const firstCol: ColDef<ScheduleGridRow> = {
    headerName: "Сотрудник",
    field: "fio",
    pinned: "left",
    lockPinned: true,
    width: 280,
    minWidth: 260,
    maxWidth: 320,
    resizable: false,
    sortable: false,
    cellRenderer: EmployeeInfoCellRenderer,
    editable: false,
  };

  const dayCols: ColDef<ScheduleGridRow>[] = dates.map((date, i) => ({
    headerName: formatHeaderDate(date),
    field: `d${i}` as keyof ScheduleGridRow,
    width: 60,
    minWidth: 60,
    maxWidth: 60,
    resizable: false,
    sortable: false,
    suppressMovable: true,
    editable: false,
    wrapHeaderText: false,
    autoHeaderHeight: false,
    cellRenderer: ScheduleDayCellRenderer,
    tooltipValueGetter: () => formatTooltipDate(date),
  }));

  return [firstCol, ...dayCols];
}

