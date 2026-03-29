import type { ScheduleDayCell } from "@/pages/schedule/ScheduleDayCellRenderer";

export type ExcelSubRow = "marks" | "codes" | "hours";

/** Одна визуальная строка сетки (метки / коды / часы). */
export type ExcelScheduleRow = {
  rowKey: string;
  employeeId: string;
  subRow: ExcelSubRow;
  templateLabel: string;
  fio: string;
  tabNumber: string;
  position: string;
  grade: string;
  gender: string;
  /** Ячейки года по индексу дня (0 = 1 янв), только для чтения в cellClass / valueGetter */
  _cells: (ScheduleDayCell | null)[];
};
