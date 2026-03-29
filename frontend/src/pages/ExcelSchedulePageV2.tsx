import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import {
  computeCodeRuns,
  EXCEL_V2_MONTH,
  EXCEL_V2_YEAR,
  extractHolidayDayIndicesV2,
  formatHoursV2,
  formatMarksV2,
  getMonthDays,
  parseExcelV2Employees,
  type ExcelV2CodeRun,
  type ExcelV2EmployeeBlock,
  type ExcelV2MonthDay,
} from "@/pages/schedule/excelScheduleV2Data";
import { getScheduleGrid } from "@/shared/api/schedule/api";

import "@/pages/schedule/excelScheduleV2.css";

const MONTH_NAMES = [
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

function marksTextForRun(run: ExcelV2CodeRun): string {
  return run.cells.map(formatMarksV2).filter(Boolean).join(" · ");
}

function hoursTextForRun(run: ExcelV2CodeRun): string {
  return run.cells.map(formatHoursV2).filter(Boolean).join(" ");
}

function hasAnyMarks(runs: ExcelV2CodeRun[]): boolean {
  return runs.some((run) => marksTextForRun(run).trim() !== "");
}

function hasAnyHours(runs: ExcelV2CodeRun[]): boolean {
  return runs.some((run) => hoursTextForRun(run).trim() !== "");
}

function runFlags(run: ExcelV2CodeRun, monthDays: ExcelV2MonthDay[], holidaySet: Set<number>) {
  const slice = monthDays.slice(run.startIdx, run.startIdx + run.length);
  const allWknd = slice.length > 0 && slice.every((d) => d.isWeekend);
  const anyHol = slice.some((d) => holidaySet.has(d.dayIndex));
  return { slice, allWknd, anyHol };
}

function tdPropsForRun(
  run: ExcelV2CodeRun,
  monthDays: ExcelV2MonthDay[],
  holidaySet: Set<number>,
  rowClass: "marks" | "codes" | "hours",
): { className: string; style?: CSSProperties; children: React.ReactNode } {
  const { allWknd, anyHol } = runFlags(run, monthDays, holidaySet);
  const first = run.cells[0] ?? null;

  const parts = ["excel-v2-day", `excel-v2-row-${rowClass}`];
  let colorClass = "";

  if (rowClass === "codes") {
    const code = (first?.code ?? "").toUpperCase();

    if (code === "В") colorClass = "excel-code-v";
    else if (code === "ОТ") colorClass = "excel-code-ot";
    else if (code === "Д") colorClass = "";
    else if (code) colorClass = "excel-code-other";
  }

  if (colorClass) parts.push(colorClass);
  if (allWknd) parts.push("excel-v2-run-all-wknd");
  if (anyHol) parts.push("excel-v2-run-hol");

  const style: CSSProperties = {};

  let children: React.ReactNode = "";
  if (rowClass === "marks") children = marksTextForRun(run);
  else if (rowClass === "codes") children = run.codeNorm;
  else children = hoursTextForRun(run);

  return {
    className: parts.join(" "),
    style: Object.keys(style).length ? style : undefined,
    children,
  };
}

export function ExcelSchedulePageV2() {
  const year = EXCEL_V2_YEAR;
  const month = EXCEL_V2_MONTH;

  const [blocks, setBlocks] = useState<ExcelV2EmployeeBlock[]>([]);
  const [holidaySet, setHolidaySet] = useState<Set<number>>(() => new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const monthDays = useMemo(() => getMonthDays(year, month), [year, month]);
  const monthTitle = `${MONTH_NAMES[month - 1] ?? "Месяц"} ${year}`;
  const dayCount = monthDays.length;

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    void getScheduleGrid(year)
      .then((data) => {
        setBlocks(parseExcelV2Employees(data, year));
        setHolidaySet(extractHolidayDayIndicesV2(data, year));
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Не удалось загрузить график");
      })
      .finally(() => setLoading(false));
  }, [year]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="excel-v2-page text-slate-200">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">График (табель, v2)</h1>
          <p className="mt-1 text-sm text-slate-400">
            HTML-таблица, март {year}. Источник:{" "}
            <code className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">
              GET /api/v1/schedule/grid?year={year}
            </code>
          </p>
        </div>
        <button
          type="button"
          onClick={load}
          className="rounded border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-700"
        >
          Обновить
        </button>
      </div>

      {error ? <div className="mb-4 text-sm text-red-400">{error}</div> : null}

      <div className="excel-v2-wrap excel-v2-scroll">
        {loading ? <div className="excel-v2-loading">Загрузка…</div> : null}
        {!loading ? (
          <table className="excel-v2-table">
            <thead>
              <tr>
                <th rowSpan={2} className="excel-v2-pin excel-v2-pin-h excel-v2-pin-c1">
                  Шаблон
                </th>
                <th rowSpan={2} className="excel-v2-pin excel-v2-pin-h excel-v2-pin-c2">
                  ФИО сотрудника
                </th>
                <th rowSpan={2} className="excel-v2-pin excel-v2-pin-h excel-v2-pin-c3">
                  Табельный
                </th>
                <th rowSpan={2} className="excel-v2-pin excel-v2-pin-h excel-v2-pin-c4">
                  Должность
                </th>
                <th rowSpan={2} className="excel-v2-pin excel-v2-pin-h excel-v2-pin-c5">
                  Разряд
                </th>
                <th rowSpan={2} className="excel-v2-pin excel-v2-pin-h excel-v2-pin-c6">
                  Пол
                </th>
                <th colSpan={dayCount} className="excel-v2-month-title">
                  {monthTitle}
                </th>
              </tr>
              <tr>
                {monthDays.map((d) => {
                  const hol = holidaySet.has(d.dayIndex);
                  const cls = [
                    d.isWeekend ? "excel-v2-th-wknd" : "",
                    hol ? "excel-v2-th-hol" : "",
                  ]
                    .filter(Boolean)
                    .join(" ");
                  return (
                    <th key={d.dayIndex} className={cls || undefined} title={d.date.toISOString().slice(0, 10)}>
                      {d.dom}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
			{blocks.map((emp) => {
			  const runs = computeCodeRuns(emp.marchCells);
			  const showMarksRow = hasAnyMarks(runs);
			  const showHoursRow = hasAnyHours(runs);
			  const pinnedRowSpan = 1 + (showMarksRow ? 1 : 0) + (showHoursRow ? 1 : 0);

			  return (
				<Fragment key={emp.employeeId}>
				  {showMarksRow ? (
					<tr className="excel-v2-body-group excel-v2-row-marks">
					  <td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c1" title={emp.templateLabel}>
						{emp.templateLabel}
					  </td>
					  <td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c2" title={emp.fio}>
						{emp.fio}
					  </td>
					  <td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c3">
						{emp.tabNumber}
					  </td>
					  <td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c4" title={emp.position}>
						{emp.position}
					  </td>
					  <td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c5">
						{emp.grade}
					  </td>
					  <td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c6">
						{emp.gender}
					  </td>
					  {runs.map((run, i) => {
						const p = tdPropsForRun(run, monthDays, holidaySet, "marks");
						return (
						  <td key={`m-${emp.employeeId}-${i}`} colSpan={run.length} className={p.className} style={p.style}>
							{p.children}
						  </td>
						);
					  })}
					</tr>
				  ) : null}

				  <tr className="excel-v2-body-group excel-v2-row-codes">
					{!showMarksRow ? (
					  <>
						<td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c1" title={emp.templateLabel}>
						  {emp.templateLabel}
						</td>
						<td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c2" title={emp.fio}>
						  {emp.fio}
						</td>
						<td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c3">
						  {emp.tabNumber}
						</td>
						<td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c4" title={emp.position}>
						  {emp.position}
						</td>
						<td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c5">
						  {emp.grade}
						</td>
						<td rowSpan={pinnedRowSpan} className="excel-v2-pin excel-v2-pin-c6">
						  {emp.gender}
						</td>
					  </>
					) : null}

					{runs.map((run, i) => {
					  const p = tdPropsForRun(run, monthDays, holidaySet, "codes");
					  return (
						<td key={`c-${emp.employeeId}-${i}`} colSpan={run.length} className={p.className} style={p.style}>
						  {p.children}
						</td>
					  );
					})}
				  </tr>

				  {showHoursRow ? (
					<tr className="excel-v2-body-group excel-v2-row-hours">
					  {runs.map((run, i) => {
						const p = tdPropsForRun(run, monthDays, holidaySet, "hours");
						return (
						  <td key={`h-${emp.employeeId}-${i}`} colSpan={run.length} className={p.className} style={p.style}>
							{p.children}
						  </td>
						);
					  })}
					</tr>
				  ) : null}
				</Fragment>
                );
              })}
            </tbody>
          </table>
        ) : null}
      </div>
    </div>
  );
}
