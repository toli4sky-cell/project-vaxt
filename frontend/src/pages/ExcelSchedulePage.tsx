import { useCallback, useEffect, useMemo, useState } from "react";
import { AgGridReact } from "ag-grid-react";
import { AllCommunityModule, ModuleRegistry } from "ag-grid-community";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";

import { buildExcelScheduleColumnDefs } from "@/pages/schedule/excelScheduleColumns";
import {
  EXCEL_SCHEDULE_YEAR,
  extractHolidayDayIndices,
  normalizeExcelScheduleApiPayload,
} from "@/pages/schedule/excelScheduleData";
import type { ExcelScheduleRow } from "@/pages/schedule/excelScheduleTypes";
import { getScheduleGrid } from "@/shared/api/schedule/api";

import "@/pages/schedule/excelSchedule.css";

ModuleRegistry.registerModules([AllCommunityModule]);

const DEFAULT_MONTH = 3;

export function ExcelSchedulePage() {
  const year = EXCEL_SCHEDULE_YEAR;
  const month = DEFAULT_MONTH;

  const [rowData, setRowData] = useState<ExcelScheduleRow[]>([]);
  const [holidayDayIndices, setHolidayDayIndices] = useState<Set<number>>(() => new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const columnDefs = useMemo(
    () => buildExcelScheduleColumnDefs(year, month, holidayDayIndices),
    [year, month, holidayDayIndices],
  );

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    void getScheduleGrid(year)
      .then((data) => {
        setRowData(normalizeExcelScheduleApiPayload(data));
        setHolidayDayIndices(extractHolidayDayIndices(data, year));
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
    <div className="excel-schedule-page text-slate-200">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">График (Excel-вид)</h1>
          <p className="mt-1 text-sm text-slate-400">
            Месяц: март {year}. Данные:{" "}
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

      <div
        className="excel-schedule-shell excel-ag ag-theme-quartz border border-slate-700 bg-slate-900/40"
        style={{ height: "min(78vh, 880px)", width: "100%", minHeight: 420 }}
      >
        <AgGridReact<ExcelScheduleRow>
          columnDefs={columnDefs}
          rowData={rowData}
          loading={loading}
          getRowId={(p) => p.data.rowKey}
          defaultColDef={{
            editable: false,
            sortable: false,
            resizable: false,
          }}
          rowHeight={23}
          headerHeight={22}
          groupHeaderHeight={24}
          suppressCellFocus
          suppressRowClickSelection
          suppressDragLeaveHidesColumns
          domLayout="normal"
          animateRows={false}
          enableCellTextSelection
        />
      </div>
    </div>
  );
}
