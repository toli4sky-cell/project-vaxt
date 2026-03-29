import type { CellClassParams, ColDef, ColGroupDef } from "ag-grid-community";
import { getScheduleCellBgClass } from "@/pages/schedule/ScheduleDayCellRenderer";
import { dayValueForSubRow } from "@/pages/schedule/excelScheduleData";
import type { ExcelScheduleRow } from "@/pages/schedule/excelScheduleTypes";

const MONTH_LONG = [
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

function pinnedCellClass(colId: string, p: CellClassParams<ExcelScheduleRow, unknown>): string {
  const row = p.data;
  if (!row) return "excel-pinned";

  const parts = ["excel-pinned", `excel-pinned-${colId}`, `excel-sub-${row.subRow}`];

  // скрываем дублирующиеся значения (оставляем только в первой строке блока)
  if (row.subRow !== "marks") {
    parts.push("excel-hide-duplicate");
  }

  return parts.join(" ");
}

function isWeekendDate(d: Date): boolean {
  const day = d.getDay();
  return day === 0 || day === 6;
}

export function buildExcelScheduleColumnDefs(
  year: number,
  month: number,
  holidayDayIndices: Set<number>,
): Array<ColDef<ExcelScheduleRow> | ColGroupDef<ExcelScheduleRow>> {
  const last = new Date(year, month, 0).getDate();
  const dayEntries: { date: Date; dayIndex: number }[] = [];
  for (let d = 1; d <= last; d++) {
    const date = new Date(year, month - 1, d);
    const start = new Date(year, 0, 1);
    const dayIndex = Math.round((date.getTime() - start.getTime()) / 86400000);
    dayEntries.push({ date, dayIndex });
  }

  const monthTitle = `${MONTH_LONG[month - 1] ?? "Месяц"} ${year}`;

  const pinnedDefs: ColDef<ExcelScheduleRow>[] = [
    {
      colId: "tpl",
      headerName: "Шаблон",
      width: 100,
      minWidth: 88,
      maxWidth: 140,
      pinned: "left",
      lockPinned: true,
	  valueGetter: (p) => p.data?.templateLabel ?? "",
      cellClass: (p) => pinnedCellClass("tpl", p),
      suppressMovable: true,
      sortable: false,
      resizable: false,
    },
    {
      colId: "fio",
      headerName: "ФИО сотрудника",
      width: 200,
      minWidth: 160,
      maxWidth: 280,
      pinned: "left",
      lockPinned: true,
      valueGetter: (p) => p.data?.fio ?? "",
      cellClass: (p) => pinnedCellClass("fio", p),
      suppressMovable: true,
      sortable: false,
      resizable: false,
    },
    {
      colId: "tab",
      headerName: "Табельный",
      width: 92,
      minWidth: 80,
      maxWidth: 110,
      pinned: "left",
      lockPinned: true,
	  valueGetter: (p) => p.data?.tabNumber ?? "",
      cellClass: (p) => pinnedCellClass("tab", p),
      suppressMovable: true,
      sortable: false,
      resizable: false,
    },
    {
      colId: "pos",
      headerName: "Должность",
      width: 150,
      minWidth: 120,
      maxWidth: 220,
      pinned: "left",
      lockPinned: true,
	  valueGetter: (p) => p.data?.position ?? "",
      cellClass: (p) => pinnedCellClass("pos", p),
      suppressMovable: true,
      sortable: false,
      resizable: false,
    },
    {
      colId: "grade",
      headerName: "Разряд",
      width: 72,
      minWidth: 64,
      maxWidth: 88,
      pinned: "left",
      lockPinned: true,
	  valueGetter: (p) => p.data?.grade ?? "",
      cellClass: (p) => pinnedCellClass("grade", p),
      suppressMovable: true,
      sortable: false,
      resizable: false,
    },
    {
      colId: "gender",
      headerName: "Пол",
      width: 52,
      minWidth: 44,
      maxWidth: 64,
      pinned: "left",
      lockPinned: true,
	  valueGetter: (p) => p.data?.gender ?? "",
      cellClass: (p) => pinnedCellClass("gender", p),
      suppressMovable: true,
      sortable: false,
      resizable: false,
    },
  ];

  const leftHeaderGroup: ColGroupDef<ExcelScheduleRow> = {
    headerName: "",
    children: pinnedDefs,
  };

  const dayChildren: ColDef<ExcelScheduleRow>[] = dayEntries.map(({ date, dayIndex }) => {
    const wknd = isWeekendDate(date);
    const isHol = holidayDayIndices.has(dayIndex);

    return {
      colId: `d${dayIndex}`,
      headerName: String(date.getDate()),
	  width: 22,
	  minWidth: 20,
	  maxWidth: 24,
      suppressMovable: true,
      sortable: false,
      resizable: false,
      valueGetter: (p) => {
        const row = p.data;
        if (!row) return "";
        const cell = row._cells[dayIndex] ?? null;
        return dayValueForSubRow(row.subRow, cell);
      },
      headerClass: ["excel-day-head", wknd ? "excel-day-head-wknd" : "", isHol ? "excel-day-head-hol" : ""]
        .filter(Boolean)
        .join(" "),
      cellStyle: (p) => {
        const row = p.data;
        if (!row) return undefined;
        const ccell = row._cells[dayIndex] ?? null;
        const st = ccell?.style_type?.trim();
        if (
          st &&
          (st.startsWith("#") || st.startsWith("rgb") || st.startsWith("rgba") || st.startsWith("hsl"))
        ) {
          return { backgroundColor: st, color: "#000" };
        }
        return undefined;
      },
      cellClass: (p: CellClassParams<ExcelScheduleRow, unknown>) => {
        const row = p.data;
        const parts = ["excel-day-cell", `excel-sub-${row?.subRow ?? "codes"}`];
        if (wknd) parts.push("excel-col-weekend");
        if (isHol) parts.push("excel-col-holiday");

        const ccell = row?._cells[dayIndex] ?? null;
        const bg = getScheduleCellBgClass(ccell);
        if (bg) parts.push(bg);

        const mergeCode = (ccell?.code ?? "").trim();
        if (mergeCode) {
          const nextCode = (row?._cells[dayIndex + 1]?.code ?? "").trim();
          if (nextCode === mergeCode) parts.push("excel-merge-with-next");
        }

        return parts.join(" ");
      },
    };
  });

  const monthGroup: ColGroupDef<ExcelScheduleRow> = {
    headerName: monthTitle,
    headerClass: "excel-month-head",
    children: dayChildren,
  };

  return [leftHeaderGroup, monthGroup];
}
