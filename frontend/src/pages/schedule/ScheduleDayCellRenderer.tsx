import type { ICellRendererParams } from "ag-grid-community";

export type ScheduleDayCell = {
  top_text?: string | null;
  overlay_code?: string | null;
  code?: string | null;
  total_hours?: number | string | null;
  day_hours?: number | string | null;
  night_hours?: number | string | null;
  style_type?: string | null;
  weekend?: boolean | null;
  holiday?: boolean | null;
};

export type ScheduleGridRow = {
  id: string | number;
  fio: string;
  tabNumber: string;
  department: string;
} & Record<`d${number}`, ScheduleDayCell | null>;

/**
 * Класс для `cellClass` у самой ячейки AG Grid (заливка только на `.ag-cell`, не во внутреннем DOM).
 */
export function getScheduleCellBgClass(cell: ScheduleDayCell | null | undefined): string {
  if (!cell) return "";

  const stRaw = cell.style_type?.trim();
  if (stRaw) {
    if (
      stRaw.startsWith("#") ||
      stRaw.startsWith("rgb") ||
      stRaw.startsWith("rgba") ||
      stRaw.startsWith("hsl") ||
      stRaw.startsWith("hsla")
    ) {
      return "";
    }
    const byKey: Record<string, string> = {
      SHIFT_A: "schedule-cell-work",
      SHIFT_B: "schedule-cell-work",
      VACATION: "schedule-cell-vac",
      MANUAL_FIX: "schedule-cell-sick",
    };
    if (byKey[stRaw]) return byKey[stRaw];
  }

  if (cell.holiday) return "schedule-cell-holiday";

  const c = cell.code?.trim() ?? "";
  if (!c) return "";

  if (c === "ОТ") return "schedule-cell-vac";
  if (c === "Б") return "schedule-cell-sick";
  if (c === "К") return "schedule-cell-trip";
  if (c === "РВД") return "schedule-cell-rvd";
  if (c === "В") return "schedule-cell-off";
  if (c === "Д") return "schedule-cell-road";
  if (c === "С") return "schedule-cell-extra";
  if (c === "НВ") return "schedule-cell-nv";
  if (c === "4" || c === "5" || c === "6" || /^[0-9]+$/.test(c)) return "schedule-cell-work";
  return "schedule-cell-work";
}

function formatHours(v: number | string | null | undefined): string {
  if (v === null || v === undefined || v === "") return "";
  if (typeof v === "number") return v.toString();
  return String(v);
}

/**
 * Ровно один корневой `div` без вложенных контейнеров-карточек; только `span` для строк текста.
 * Цвет фона — только через `cellClass` / `cellStyle` на ячейке сетки.
 */
export function ScheduleDayCellRenderer(
  props: ICellRendererParams<ScheduleGridRow, ScheduleDayCell | null>,
) {
  const cell = props.value;
  if (!cell) {
    return <div className="schedule-cell-root" />;
  }

  const overlay = cell.overlay_code ?? null;
  const topText = cell.top_text ?? null;
  const topLine = [overlay, topText].filter(Boolean).join(" ");
  const code = cell.code ?? null;
  const hoursText = formatHours(cell.total_hours);

  return (
    <div className="schedule-cell-root">
      {topLine ? <span className="schedule-cell-overlay">{topLine}</span> : null}
      <span className="schedule-cell-code">{code ?? ""}</span>
      {hoursText ? <span className="schedule-cell-hours">{hoursText}</span> : null}
    </div>
  );
}
