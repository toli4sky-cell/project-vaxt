import { dayIndexInYear, getScheduleDates, SCHEDULE_DAYS_COUNT } from "@/pages/schedule/scheduleGridConfig";
import type { ScheduleDayCell } from "@/pages/schedule/ScheduleDayCellRenderer";

export const EXCEL_V2_YEAR = 2026;
export const EXCEL_V2_MONTH = 3;

function isWeekendDate(d: Date): boolean {
  const day = d.getDay();
  return day === 0 || day === 6;
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

function isZeroLike(v: unknown): boolean {
  if (v === null || v === undefined) return true;
  const s = String(v).trim().replace(",", ".");
  if (s === "") return true;
  const n = Number(s);
  return Number.isFinite(n) && n === 0;
}

export function formatMarksV2(cell: ScheduleDayCell | null): string {
  if (!cell) return "";
  const parts: string[] = [];
  if (cell.overlay_code) parts.push(String(cell.overlay_code));
  if (cell.top_text) parts.push(String(cell.top_text));
  if (!isZeroLike(cell.night_hours)) {
    parts.push(`н${cell.night_hours}`);
  }
  return parts.join(" ");
}

export function formatHoursV2(cell: ScheduleDayCell | null): string {
  if (!cell) return "";
  if (isZeroLike(cell.total_hours)) return "";
  return String(cell.total_hours);
}

function buildYearCells(emp: Record<string, unknown>, year: number): (ScheduleDayCell | null)[] {
  const dates = getScheduleDates(year, SCHEDULE_DAYS_COUNT);
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
      if (p.length >= 3 && !Number.isNaN(p[0]) && p[0] === year) {
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

export type ExcelV2MonthDay = {
  dom: number;
  dayIndex: number;
  date: Date;
  isWeekend: boolean;
};

export function getMonthDays(year: number, month: number): ExcelV2MonthDay[] {
  const last = new Date(year, month, 0).getDate();
  const out: ExcelV2MonthDay[] = [];
  for (let d = 1; d <= last; d++) {
    const date = new Date(year, month - 1, d);
    out.push({
      dom: d,
      dayIndex: dayIndexInYear(year, month, d),
      date,
      isWeekend: isWeekendDate(date),
    });
  }
  return out;
}

export type ExcelV2CodeRun = {
  startIdx: number;
  length: number;
  codeNorm: string;
  cells: (ScheduleDayCell | null)[];
};

/** Группировка подряд одинаковых кодов (включая пустые). */
export function computeCodeRuns(marchCells: (ScheduleDayCell | null)[]): ExcelV2CodeRun[] {
  const runs: ExcelV2CodeRun[] = [];
  let i = 0;
  while (i < marchCells.length) {
    const codeNorm = (marchCells[i]?.code ?? "").trim();
    let j = i + 1;
    while (j < marchCells.length && (marchCells[j]?.code ?? "").trim() === codeNorm) {
      j++;
    }
    runs.push({
      startIdx: i,
      length: j - i,
      codeNorm,
      cells: marchCells.slice(i, j),
    });
    i = j;
  }
  return runs;
}

export type ExcelV2EmployeeBlock = {
  employeeId: string;
  templateLabel: string;
  fio: string;
  tabNumber: string;
  position: string;
  grade: string;
  gender: string;
  /** Ячейки марта по порядку 1..last (синхронно с getMonthDays). */
  marchCells: (ScheduleDayCell | null)[];
};

export function extractHolidayDayIndicesV2(data: unknown, year: number): Set<number> {
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

export function parseExcelV2Employees(data: unknown, year: number): ExcelV2EmployeeBlock[] {
  const raw = data as Record<string, unknown>;
  const rowsUnknown = raw?.rows ?? raw?.data ?? [];
  if (!Array.isArray(rowsUnknown)) return [];

  const employeesExtra = Array.isArray(raw?.employees) ? (raw.employees as Record<string, unknown>[]) : [];

  const monthDays = getMonthDays(year, EXCEL_V2_MONTH);

  return (rowsUnknown as Record<string, unknown>[]).map((emp, empIdx) => {
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

    const yearCells = buildYearCells(emp, year);
    const marchCells = monthDays.map(({ dayIndex }) => yearCells[dayIndex] ?? null);

    return {
      employeeId,
      templateLabel,
      fio,
      tabNumber,
      position: position || "—",
      grade,
      gender,
      marchCells,
    };
  });
}

export function isCustomStyleColor(styleType: string | undefined | null): string | null {
  const st = styleType?.trim();
  if (!st) return null;
  if (
    st.startsWith("#") ||
    st.startsWith("rgb") ||
    st.startsWith("rgba") ||
    st.startsWith("hsl") ||
    st.startsWith("hsla")
  ) {
    return st;
  }
  return null;
}
