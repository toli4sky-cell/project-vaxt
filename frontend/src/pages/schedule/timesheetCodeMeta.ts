/** Локальные подписи кодов Т-12 (как в seed) — для tooltip без запроса к API. */
export const TIMESHEET_CODE_DESCRIPTION: Record<string, string> = {
  В: "Выходной день",
  Д: "День дороги",
  ОТ: "Отпуск",
  Б: "Больничный",
  К: "Командировка",
  РВД: "Работа в выходной день",
  С: "Сверхурочные",
  НВ: "Неявка без сохранения заработной платы",
  "4": "Рабочий день / смена (код 4)",
  "5": "Рабочий день / смена (код 5)",
  "6": "Рабочий день / смена (код 6)",
};

export function getCodeDescription(code: string | null | undefined): string {
  if (!code) return "—";
  const c = code.trim();
  if (TIMESHEET_CODE_DESCRIPTION[c]) return TIMESHEET_CODE_DESCRIPTION[c];
  if (/^[0-9]+$/.test(c)) return `Рабочее время (${c})`;
  return c;
}
