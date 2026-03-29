import type { ITooltipParams } from "ag-grid-community";
import type { ScheduleDayCell, ScheduleGridRow } from "@/pages/schedule/ScheduleDayCellRenderer";
import { getScheduleDates, SCHEDULE_DAYS_COUNT } from "@/pages/schedule/scheduleGridConfig";
import { getCodeDescription } from "@/pages/schedule/timesheetCodeMeta";

function formatNum(v: number | string | null | undefined): string {
  if (v === null || v === undefined || v === "") return "—";
  return String(v);
}

export function ScheduleCellTooltip(props: ITooltipParams<ScheduleGridRow, ScheduleDayCell | null>) {
  const colId =
  props.column && "getColId" in props.column
    ? (props.column as any).getColId()
    : "";
  const ctx = props.context as { year?: number } | undefined;
  const year = ctx?.year ?? 2026;

  if (colId === "employee") {
    const row = props.data;
    if (!row) return null;
    return (
      <div className="schedule-tooltip max-w-[320px] rounded border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 shadow-md">
        <div className="font-semibold text-slate-900">{row.fio}</div>
        <div className="mt-1">Таб. {row.tabNumber}</div>
        {row.department ? <div className="mt-0.5 text-slate-600">{row.department}</div> : null}
      </div>
    );
  }

  let dateLabel = "—";
  const m = /^d(\d+)$/.exec(colId);
  if (m) {
    const idx = parseInt(m[1], 10);
    const dates = getScheduleDates(year, SCHEDULE_DAYS_COUNT);
    const d = dates[idx];
    if (d) {
      const dd = String(d.getDate()).padStart(2, "0");
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      dateLabel = `${dd}.${mm}.${d.getFullYear()}`;
    }
  }

  const cell = props.value;
  if (!cell) {
    return (
      <div className="schedule-tooltip max-w-[280px] rounded border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 shadow-md">
        <div className="font-semibold text-slate-900">Дата: {dateLabel}</div>
        <div className="mt-1 text-slate-500">Пусто</div>
      </div>
    );
  }

  const code = cell?.code ?? null;
  const desc = getCodeDescription(code);

  return (
    <div className="schedule-tooltip max-w-[300px] rounded border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 shadow-md">
      <div className="border-b border-slate-100 pb-1.5 font-semibold text-slate-900">{dateLabel}</div>
      <dl className="mt-2 space-y-1">
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Код</dt>
          <dd className="text-right font-medium">{code ?? "—"}</dd>
        </div>
        <div className="text-[11px] leading-snug text-slate-600">{desc}</div>
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Надстройка</dt>
          <dd className="text-right">{cell?.overlay_code ?? "—"}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Верхний текст</dt>
          <dd className="max-w-[160px] text-right break-words">{cell?.top_text ?? "—"}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Часы (всего)</dt>
          <dd className="text-right">{formatNum(cell?.total_hours)}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Дневные</dt>
          <dd className="text-right">{formatNum(cell?.day_hours)}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Ночные</dt>
          <dd className="text-right">{formatNum(cell?.night_hours)}</dd>
        </div>
        {cell?.style_type ? (
          <div className="flex justify-between gap-3">
            <dt className="text-slate-500">Стиль</dt>
            <dd className="text-right text-[11px]">{cell.style_type}</dd>
          </div>
        ) : null}
      </dl>
    </div>
  );
}
