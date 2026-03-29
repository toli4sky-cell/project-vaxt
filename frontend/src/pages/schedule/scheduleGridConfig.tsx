import type { CellClassParams, ColDef, ColGroupDef } from "ag-grid-community";
import {
  getScheduleCellBgClass,
  ScheduleDayCellRenderer,
  type ScheduleDayCell,
  type ScheduleGridRow,
} from "@/pages/schedule/ScheduleDayCellRenderer";

export const SCHEDULE_DAYS_COUNT = 365;

export type ScheduleViewMode = "year" | "month";

/** Контекст AG Grid: hover + год для tooltip / стилей */
export type ScheduleGridHoverContext = {
  year: number;
  hoveredColId: string | null;
  hoverCellKey: string | null;
};

const MONTH_HEADER_SHORT = [
  "Янв",
  "Фев",
  "Мар",
  "Апр",
  "Май",
  "Июн",
  "Июл",
  "Авг",
  "Сен",
  "Окт",
  "Ноя",
  "Дек",
] as const;

const MONTH_HEADER_LONG = [
  "Январь",
  "Февраль",
  "Март",
  "Апрель",
  "Май",
  "Июнь",
  "Июль",
  "Август",
  "Сентябрь",
  "Октябрь",
  "Ноябрь",
  "Декабрь",
] as const;

function isWeekendDate(d: Date): boolean {
  const day = d.getDay();
  return day === 0 || day === 6;
}

export function dayIndexInYear(year: number, month: number, day: number): number {
  const start = new Date(year, 0, 1);
  const cur = new Date(year, month - 1, day);
  return Math.round((cur.getTime() - start.getTime()) / 86400000);
}

export function getScheduleDates(year: number, daysCount: number = SCHEDULE_DAYS_COUNT): Date[] {
  const start = new Date(year, 0, 1);
  const dates: Date[] = [];
  for (let i = 0; i < daysCount; i++) {
    dates.push(new Date(start.getFullYear(), start.getMonth(), start.getDate() + i));
  }
  return dates;
}

export function getMonthDatesWithIndices(year: number, month: number): { date: Date; dayIndex: number }[] {
  const last = new Date(year, month, 0).getDate();
  const out: { date: Date; dayIndex: number }[] = [];
  for (let d = 1; d <= last; d++) {
    const date = new Date(year, month - 1, d);
    out.push({ date, dayIndex: dayIndexInYear(year, month, d) });
  }
  return out;
}

function formatTooltipDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function EmployeeInfoCellRenderer(params: { data: ScheduleGridRow | undefined }) {
  const row = params.data;
  if (!row) return null;

  return (
    <div className="flex h-full flex-col justify-center gap-0.5 px-2.5 py-1 leading-tight">
      <div className="truncate text-[12px] font-semibold text-slate-900">{row.fio}</div>
      <div className="truncate text-[11px] text-slate-700">Таб. {row.tabNumber}</div>
      <div className="line-clamp-2 text-[10px] leading-snug text-slate-600" title={row.department}>
        {row.department}
      </div>
    </div>
  );
}

function buildDayColumn(
  date: Date,
  dayIndex: number,
  holidayDayIndices: Set<number>,
): ColDef<ScheduleGridRow> {
  const wknd = isWeekendDate(date);
  const isMonthStart = date.getDate() === 1;
  const isHolidayCol = holidayDayIndices.has(dayIndex);

  const headerClass = [
    "schedule-day-header",
    wknd ? "schedule-header-weekend" : "",
    isHolidayCol ? "schedule-header-holiday" : "",
    isMonthStart ? "schedule-header-month-start" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return {
    headerName: String(date.getDate()),
    colId: `d${dayIndex}`,
    field: `d${dayIndex}` as keyof ScheduleGridRow,
    width: 36,
    minWidth: 34,
    maxWidth: 38,
    resizable: false,
    sortable: false,
    suppressMovable: true,
    editable: false,
    suppressHeaderMenuButton: true,
    wrapHeaderText: false,
    autoHeaderHeight: false,
    cellRenderer: ScheduleDayCellRenderer,
    headerTooltip: formatTooltipDate(date),
    headerClass,
    cellStyle: (p) => {
      const dayField = `d${dayIndex}` as keyof ScheduleGridRow;
      const dayCell = p.data?.[dayField] as ScheduleDayCell | null | undefined;
      const st = dayCell?.style_type?.trim();
      if (
        st &&
        (st.startsWith("#") || st.startsWith("rgb") || st.startsWith("rgba") || st.startsWith("hsl"))
      ) {
        return { backgroundColor: st, color: "#4b5563" };
      }
      return undefined;
    },
    cellClass: (p: CellClassParams<ScheduleGridRow, unknown>) => {
      const parts = ["schedule-day-col"];
      if (wknd) parts.push("schedule-col-weekend");
      if (isHolidayCol) parts.push("schedule-col-holiday");
      if (isMonthStart) parts.push("schedule-col-month-start");

      const dayField = `d${dayIndex}` as keyof ScheduleGridRow;
      const prevField = `d${dayIndex - 1}` as keyof ScheduleGridRow;
      const nextField = `d${dayIndex + 1}` as keyof ScheduleGridRow;

      const curr = p.data?.[dayField] as ScheduleDayCell | null | undefined;
      const prev = p.data?.[prevField] as ScheduleDayCell | null | undefined;
      const next = p.data?.[nextField] as ScheduleDayCell | null | undefined;

      const tone = getScheduleCellBgClass(curr);
      if (tone) parts.push(tone);

      if (curr?.code && prev?.code === curr.code) {
        parts.push("schedule-merge-with-prev");
      }
      if (curr?.code && next?.code === curr.code) {
        parts.push("schedule-merge-with-next");
      }

      const ctx = p.context as ScheduleGridHoverContext | undefined;
      const colId = p.column?.getColId() ?? "";
      if (ctx?.hoveredColId && colId && ctx.hoveredColId === colId) {
        parts.push("schedule-col-under-cursor");
      }
      const rowId = p.data?.id != null ? String(p.data.id) : "";
      const cellKey = rowId && colId ? `${rowId}::${colId}` : "";
      if (ctx?.hoverCellKey && cellKey && ctx.hoverCellKey === cellKey) {
        parts.push("schedule-cell-hot");
      }

      return parts.join(" ");
    },
  };
}

export type ScheduleColumnOptions = {
  viewMode: ScheduleViewMode;
  month?: number;
  holidayDayIndices?: Set<number>;
};

export function getScheduleColumnDefs(
  year: number,
  opts: ScheduleColumnOptions,
): Array<ColDef<ScheduleGridRow> | ColGroupDef<ScheduleGridRow>> {
  const holidayDayIndices = opts.holidayDayIndices ?? new Set<number>();

  const firstCol: ColDef<ScheduleGridRow> = {
    colId: "employee",
    headerName: "Сотрудник",
    field: "fio",
    pinned: "left",
    lockPinned: true,
    width: 300,
    minWidth: 280,
    maxWidth: 320,
    resizable: false,
    sortable: false,
    suppressMovable: true,
    suppressHeaderMenuButton: true,
    cellRenderer: EmployeeInfoCellRenderer,
    editable: false,
    headerClass: "schedule-employee-header",
    cellClass: "schedule-employee-cell",
  };

  if (opts.viewMode === "month") {
    const m = opts.month ?? 1;
    const days = getMonthDatesWithIndices(year, m);
    const monthGroup: ColGroupDef<ScheduleGridRow> = {
      headerName: `${MONTH_HEADER_LONG[m - 1] ?? "Месяц"} ${year}`,
      children: days.map(({ date, dayIndex }) => buildDayColumn(date, dayIndex, holidayDayIndices)),
    };
    return [firstCol, monthGroup];
  }

  const monthGroups: ColGroupDef<ScheduleGridRow>[] = [];

  for (let m = 1; m <= 12; m++) {
    const days = getMonthDatesWithIndices(year, m);
    monthGroups.push({
      headerName: MONTH_HEADER_SHORT[m - 1],
      children: days.map(({ date, dayIndex }) => buildDayColumn(date, dayIndex, holidayDayIndices)),
    });
  }

  return [firstCol, ...monthGroups];
}
