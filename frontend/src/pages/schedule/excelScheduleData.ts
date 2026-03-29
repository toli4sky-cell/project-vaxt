import { dayIndexInYear, getScheduleDates, SCHEDULE_DAYS_COUNT } from "@/pages/schedule/scheduleGridConfig";
import type { ScheduleDayCell } from "@/pages/schedule/ScheduleDayCellRenderer";
import type { ExcelScheduleRow, ExcelSubRow } from "@/pages/schedule/excelScheduleTypes";

const YEAR = 2026;

function isWeekendDate(d: Date): boolean {
  const day = d.getDay();
  return day === 0 || day === 6;
}

function formatMarks(cell: ScheduleDayCell | null): string {
  if (!cell) return "";
  const parts: string[] = [];
  if (cell.overlay_code) parts.push(String(cell.overlay_code));
  if (cell.top_text) parts.push(String(cell.top_text));
  if (cell.night_hours !== null && cell.night_hours !== undefined && String(cell.night_hours) !== "") {
    parts.push(`н${cell.night_hours}`);
  }
  return parts.join(" ");
}

function formatHours(cell: ScheduleDayCell | null): string {
  if (!cell) return "";
  if (cell.total_hours === null || cell.total_hours === undefined || cell.total_hours === "") return "";
  return String(cell.total_hours);
}

function genderLabel(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  const s = String(v).toUpperCase();
  if (s === "M" || s === "MALE" || s === "М" || s === "MEN") return "М";
  if (s === "F" || s === "FEMALE" || s === "Ж" || s === "WOMEN") return "Ж";
  return String(v);
}

function pickIdNameName(obj: unknown): string {
  if (obj === null || obj === undefined) return "";
  if (typeof obj === "object" && obj !== null && "name" in obj) {
    return String((obj as { name?: string }).name ?? "");
  }
  return "";
}

/** Нормализация ответа GET /schedule/grid?year=… в плоский массив ячеек года для одного сотрудника. */
function buildYearCells(emp: Record<string, unknown>): (ScheduleDayCell | null)[] {
  const dates = getScheduleDates(YEAR, SCHEDULE_DAYS_COUNT);
  const daysRaw = emp?.days ?? emp?.cells ?? emp?.schedule ?? emp?.items ?? emp?.day_cells ?? [];
  const daysArr: unknown[] = Array.isArray(daysRaw) ? daysRaw : [];

  const cells: (ScheduleDayCell | null)[] = new Array(SCHEDULE_DAYS_COUNT).fill(null);

  for (let i = 0; i < daysArr.length; i++) {
    const baseCell = (daysArr[i] ?? {}) as Record<string, unknown>;
    let idx = i;
    const rawDate = baseCell.date;
    if (rawDate !== undefined && rawDate !== null) {
      const ds = String(rawDate).slice(0, 10);
      const p = ds.split("-").map(Number);
      if (p.length >= 3 && !Number.isNaN(p[0]) && p[0] === YEAR) {
        idx = dayIndexInYear(p[0], p[1], p[2]);
      }
    }
    if (idx < 0 || idx >= SCHEDULE_DAYS_COUNT) continue;

    const date = dates[idx];

    const holidayFromApi = baseCell?.holiday ?? baseCell?.isHoliday ?? null;
    const weekendFromApi = baseCell?.weekend ?? baseCell?.isWeekend ?? null;

    const weekend = (weekendFromApi as boolean | null) ?? isWeekendDate(date);
    const holiday = (holidayFromApi as boolean | null) ?? Boolean(baseCell?.holiday);

    const top_text =
      (baseCell?.top_text as string | null) ??
      (baseCell?.topText as string | null) ??
      (baseCell?.top as string | null) ??
      null;
    const overlay_code =
      (baseCell?.overlay_code as string | null) ??
      (baseCell?.overlayCode as string | null) ??
      (baseCell?.overlay as string | null) ??
      null;
    const code =
      (baseCell?.code as string | null) ??
      (baseCell?.shift_code as string | null) ??
      (baseCell?.shiftCode as string | null) ??
      null;
    const total_hours =
      (baseCell?.total_hours as number | string | null) ??
      (baseCell?.totalHours as number | string | null) ??
      (baseCell?.hours as number | string | null) ??
      null;
    const day_hours =
      (baseCell?.day_hours as number | string | null) ??
      (baseCell?.dayHours as number | string | null) ??
      null;
    const night_hours =
      (baseCell?.night_hours as number | string | null) ??
      (baseCell?.nightHours as number | string | null) ??
      null;
    const style_type =
      (baseCell?.style_type as string | null) ?? (baseCell?.styleType as string | null) ?? null;

    const hasVisual =
      Boolean(top_text) ||
      Boolean(overlay_code) ||
      Boolean(code) ||
      total_hours !== null ||
      day_hours !== null ||
      night_hours !== null ||
      Boolean(style_type) ||
      weekend ||
      holiday;

    cells[idx] = hasVisual
      ? {
          top_text,
          overlay_code,
          code,
          total_hours,
          day_hours,
          night_hours,
          style_type,
          weekend,
          holiday,
        }
      : null;
  }

  return cells;
}

export function normalizeExcelScheduleApiPayload(data: unknown): ExcelScheduleRow[] {
  const raw = data as Record<string, unknown>;
  const rowsUnknown = raw?.rows ?? raw?.data ?? [];
  if (!Array.isArray(rowsUnknown)) return [];

  const employeesExtra = Array.isArray(raw?.employees) ? (raw.employees as Record<string, unknown>[]) : [];

  const out: ExcelScheduleRow[] = [];

  (rowsUnknown as Record<string, unknown>[]).forEach((emp, empIdx) => {
    const idRaw = emp?.employee_id ?? emp?.id ?? emp?.employeeId ?? empIdx;
    const employeeId = String(idRaw);

    const fio: string =
      (emp?.employee_name as string) ??
      (emp?.fio as string) ??
      (emp?.full_name as string) ??
      (emp?.fullName as string) ??
      (emp?.name as string) ??
      "";

    const tabNumber: string = String(
      emp?.personnel_number ??
        emp?.tab_number ??
        emp?.tabel_number ??
        emp?.tabNumber ??
        emp?.employee_number ??
        emp?.tab ??
        "",
    );

    const position = pickIdNameName(emp?.current_position ?? emp?.position);
    const gradeRaw = emp?.current_grade ?? emp?.grade ?? null;
    const grade = gradeRaw !== null && gradeRaw !== undefined && gradeRaw !== "" ? String(gradeRaw) : "—";

    const extra = employeesExtra.find((e) => String(e?.id ?? "") === employeeId);
    const gender = genderLabel(extra?.gender ?? emp?.gender ?? (emp as { sex?: unknown }).sex);

    const templateLabel: string = String(
      emp?.schedule_template_name ??
        emp?.template_name ??
        emp?.template_label ??
        emp?.template ??
        "—",
    );

    const _cells = buildYearCells(emp);

    const subs: ExcelSubRow[] = ["marks", "codes", "hours"];
    const base = {
      employeeId,
      templateLabel,
      fio,
      tabNumber,
      position: position || "—",
      grade,
      gender,
      _cells,
    };

    for (const subRow of subs) {
      out.push({
        rowKey: `${employeeId}-${subRow}`,
        subRow,
        ...base,
      });
    }
  });

  return out;
}

export const EXCEL_SCHEDULE_YEAR = YEAR;

export function extractHolidayDayIndices(data: unknown, year: number): Set<number> {
  const raw = data as {
    reference_metadata?: { holidays?: { holiday_date: string }[] };
  };
  const set = new Set<number>();
  for (const h of raw.reference_metadata?.holidays ?? []) {
    const p = h.holiday_date.split("-").map(Number);
    if (p.length >= 3 && p[0] === year) {
      const [_, month, day] = p;
      set.add(dayIndexInYear(year, month, day));
    }
  }
  return set;
}

export function dayValueForSubRow(
  subRow: ExcelSubRow,
  cell: ScheduleDayCell | null,
): string {
  if (!cell) return "";
  if (subRow === "marks") return formatMarks(cell);
  if (subRow === "codes") return cell.code?.trim() ?? "";
  return formatHours(cell);
}
