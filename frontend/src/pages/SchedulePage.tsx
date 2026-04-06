import { useEffect, useMemo, useState } from "react";
import { AgGridReact } from "ag-grid-react";
import { AllCommunityModule, ModuleRegistry } from "ag-grid-community";
import type { ScheduleGridRow } from "@/pages/schedule/ScheduleDayCellRenderer";
import { type ScheduleDayCell as ScheduleDayCellType } from "@/pages/schedule/ScheduleDayCellRenderer";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";

import { getScheduleColumnDefs, getScheduleDates, SCHEDULE_DAYS_COUNT } from "@/pages/schedule/scheduleGridConfig";
import { getScheduleGrid } from "@/shared/api/schedule/api";

ModuleRegistry.registerModules([AllCommunityModule]);

const YEAR = 2026;

function isWeekend(date: Date): boolean {
  const day = date.getDay();
  return day === 0 || day === 6;
}

function normalizeScheduleGridData(data: unknown, year: number): ScheduleGridRow[] {
const raw = data as any;

const employeesRaw = raw?.rows ?? raw?.employees ?? raw?.data ?? [];
if (!Array.isArray(employeesRaw)) return [];

const dates = getScheduleDates(year, SCHEDULE_DAYS_COUNT);

return employeesRaw.map((emp: any, empIdx: number) => {
  const fio: string =
    emp?.fio ??
    emp?.full_name ??
    emp?.fullName ??
    emp?.employee_name ??
    emp?.name ??
    "";

  const tabNumber: string = String(
    emp?.personnel_number ??
    emp?.tab_number ??
    emp?.tabel_number ??
    emp?.tabNumber ??
    emp?.employee_number ??
    emp?.tab ??
    ""
  );

  const department: string =
    emp?.current_department?.name ??
    emp?.department?.name ??
    emp?.department ??
    emp?.division ??
    emp?.department_name ??
    emp?.dept ??
    "";

  const daysRaw = emp?.days ?? emp?.cells ?? emp?.schedule ?? emp?.items ?? emp?.day_cells ?? [];
  const daysArr: any[] = Array.isArray(daysRaw) ? daysRaw : [];

  const row: Partial<ScheduleGridRow> & Record<string, any> = {
    id: emp?.id ?? emp?.employee_id ?? empIdx,
    fio,
    tabNumber,
    department,
  };

  for (let i = 0; i < SCHEDULE_DAYS_COUNT; i++) {
    const date = dates[i];
    const baseCell = daysArr[i] ?? {};

    const holidayFromApi = baseCell?.holiday ?? baseCell?.isHoliday ?? null;
    const weekendFromApi = baseCell?.weekend ?? baseCell?.isWeekend ?? null;

    const weekend = weekendFromApi ?? isWeekend(date);
    const holiday = holidayFromApi ?? Boolean(baseCell?.holiday);

    const top_text = baseCell?.top_text ?? baseCell?.topText ?? baseCell?.top ?? null;
    const overlay_code = baseCell?.overlay_code ?? baseCell?.overlayCode ?? baseCell?.overlay ?? null;
    const code = baseCell?.code ?? baseCell?.shift_code ?? baseCell?.shiftCode ?? null;
    const total_hours = baseCell?.total_hours ?? baseCell?.totalHours ?? baseCell?.hours ?? null;
    const style_type = baseCell?.style_type ?? baseCell?.styleType ?? null;

    const hasVisual =
      Boolean(top_text) ||
      Boolean(overlay_code) ||
      Boolean(code) ||
      total_hours !== null ||
      Boolean(style_type) ||
      weekend ||
      holiday;

    const dayCell: ScheduleDayCellType = {
      top_text,
      overlay_code,
      code,
      total_hours,
      style_type,
      weekend,
      holiday,
    };

    row[`d${i}`] = hasVisual ? dayCell : null;
  }

  return row as ScheduleGridRow;
});
}

export function SchedulePage() {
  const columnDefs = useMemo(() => getScheduleColumnDefs(YEAR), []);

  const [rowData, setRowData] = useState<ScheduleGridRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    void getScheduleGrid(YEAR)
      .then((data) => {
        if (cancelled) return;
        setRowData(normalizeScheduleGridData(data, YEAR));
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Не удалось загрузить график");
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-white">Schedule Grid ({YEAR})</h1>
      <p className="mt-2 text-slate-400">
        Годовой график: строки — сотрудники, колонки — даты.
      </p>

      {error ? <div className="mt-4 text-sm text-red-400">{error}</div> : null}

      <div className="ag-theme-quartz mt-6" style={{ height: 720, width: "100%" }}>
        <AgGridReact<ScheduleGridRow>
          columnDefs={columnDefs}
          rowData={rowData}
          defaultColDef={{
            editable: false,
            sortable: false,
            resizable: false,
          }}
          rowHeight={68}
          headerHeight={36}
          suppressCellFocus={true}
          suppressRowClickSelection={true}
          suppressDragLeaveHidesColumns={true}
          domLayout="normal"
          loadingOverlayComponent={() => (loading ? <div className="text-slate-300">Загрузка…</div> : null)}
        />
      </div>
    </div>
  );
}

