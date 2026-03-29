import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AgGridReact } from "ag-grid-react";
import type { CellMouseOverEvent, GridApi } from "ag-grid-community";
import { AllCommunityModule, ModuleRegistry } from "ag-grid-community";
import type { ScheduleGridRow } from "@/pages/schedule/ScheduleDayCellRenderer";
import { type ScheduleDayCell as ScheduleDayCellType } from "@/pages/schedule/ScheduleDayCellRenderer";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";
import "@/pages/schedule/scheduleSheet.css";

import { ScheduleCellTooltip } from "@/pages/schedule/ScheduleCellTooltip";
import { ScheduleGridLegend } from "@/pages/schedule/ScheduleGridLegend";
import { ScheduleGridToolbar } from "@/pages/schedule/ScheduleGridToolbar";
import {
  dayIndexInYear,
  getScheduleColumnDefs,
  getScheduleDates,
  SCHEDULE_DAYS_COUNT,
  type ScheduleViewMode,
} from "@/pages/schedule/scheduleGridConfig";
import { getScheduleGrid } from "@/shared/api/schedule/api";

ModuleRegistry.registerModules([AllCommunityModule]);

const YEAR = 2026;

function defaultMonthForYear(year: number): number {
  const now = new Date();
  if (now.getFullYear() === year) return now.getMonth() + 1;
  return 1;
}

function extractHolidayDayIndices(data: unknown, year: number): Set<number> {
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

function isWeekend(date: Date): boolean {
  const day = date.getDay();
  return day === 0 || day === 6;
}

function normalizeScheduleGridData(data: unknown): ScheduleGridRow[] {
  const raw = data as Record<string, unknown>;

	const employeesRawUnknown = raw?.rows ?? raw?.employees ?? raw?.data ?? [];
	if (!Array.isArray(employeesRawUnknown)) return [];

	const employeesRaw = employeesRawUnknown as Record<string, unknown>[];

	return employeesRaw.map((emp, empIdx) => {
    const fio: string =
      (emp?.fio as string) ??
      (emp?.full_name as string) ??
      (emp?.fullName as string) ??
      (emp?.employee_name as string) ??
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

    const deptRaw = emp?.current_department ?? emp?.department;
    const department: string =
      (typeof deptRaw === "object" && deptRaw !== null && "name" in deptRaw
        ? (deptRaw as { name?: string }).name
        : undefined) ??
      (emp?.department as string) ??
      (emp?.division as string) ??
      (emp?.department_name as string) ??
      (emp?.dept as string) ??
      "";

    const daysRaw = emp?.days ?? emp?.cells ?? emp?.schedule ?? emp?.items ?? emp?.day_cells ?? [];
    const daysArr: unknown[] = Array.isArray(daysRaw) ? daysRaw : [];

    const row: Partial<ScheduleGridRow> & Record<string, unknown> = {
      id: (emp?.id as string | number) ?? (emp?.employee_id as string | number) ?? empIdx,
      fio,
      tabNumber,
      department,
    };

	const dates = getScheduleDates(YEAR, SCHEDULE_DAYS_COUNT);

    for (let i = 0; i < SCHEDULE_DAYS_COUNT; i++) {
      const date = dates[i];
      const baseCell = (daysArr[i] ?? {}) as Record<string, unknown>;

      const holidayFromApi = baseCell?.holiday ?? baseCell?.isHoliday ?? null;
      const weekendFromApi = baseCell?.weekend ?? baseCell?.isWeekend ?? null;

      const weekend = (weekendFromApi as boolean | null) ?? isWeekend(date);
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

      const dayCell: ScheduleDayCellType = {
        top_text,
        overlay_code,
        code,
        total_hours,
        day_hours,
        night_hours,
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
  const [viewMode, setViewMode] = useState<ScheduleViewMode>("month");
  const [month, setMonth] = useState(() => defaultMonthForYear(YEAR));
  const [rowData, setRowData] = useState<ScheduleGridRow[]>([]);
  const [holidayDayIndices, setHolidayDayIndices] = useState<Set<number>>(() => new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const [hoveredColId, setHoveredColId] = useState<string | null>(null);
  const [hoverCellKey, setHoverCellKey] = useState<string | null>(null);

  const gridApiRef = useRef<GridApi<ScheduleGridRow> | null>(null);

  const columnDefs = useMemo(
    () => getScheduleColumnDefs(YEAR, { viewMode, month, holidayDayIndices }),
    [viewMode, month, holidayDayIndices],
  );

  const gridContext = useMemo(
    () =>
      ({
        year: YEAR,
        hoveredColId,
        hoverCellKey,
      }) as const,
    [hoveredColId, hoverCellKey],
  );

  useEffect(() => {
    gridApiRef.current?.refreshCells({ force: true });
  }, [hoveredColId, hoverCellKey, columnDefs]);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    void getScheduleGrid(YEAR)
      .then((data) => {
        setRowData(normalizeScheduleGridData(data));
        setHolidayDayIndices(extractHolidayDayIndices(data, YEAR));
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Не удалось загрузить график");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  const onRefresh = () => setRefreshKey((k) => k + 1);

  const onCellMouseOver = useCallback((e: CellMouseOverEvent<ScheduleGridRow>) => {
    const colId = e.column?.getColId() ?? "";
    if (!colId || colId === "employee") {
      setHoveredColId(null);
      setHoverCellKey(null);
      return;
    }
    const rowId = e.data?.id != null ? String(e.data.id) : "";
    setHoveredColId(colId);
    setHoverCellKey(rowId ? `${rowId}::${colId}` : null);
  }, []);

  const clearHover = useCallback(() => {
    setHoveredColId(null);
    setHoverCellKey(null);
  }, []);

  return (
    <div>
      {error ? <div className="mb-4 text-sm text-red-400">{error}</div> : null}

      <div
        className="schedule-workbench rounded-lg border border-slate-300 bg-slate-50"
        onMouseLeave={clearHover}
      >
        <ScheduleGridToolbar
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          month={month}
          onMonthChange={setMonth}
          year={YEAR}
          employeeCount={rowData.length}
          loading={loading}
          onRefresh={onRefresh}
        />
        <ScheduleGridLegend />
        <div
          className="schedule-grid-excel ag-theme-quartz px-1 pb-1"
          style={{ height: "min(74vh, 820px)", width: "100%", minHeight: 400 }}
        >
          <AgGridReact<ScheduleGridRow>
            columnDefs={columnDefs}
            rowData={rowData}
            loading={loading}
            context={gridContext}
            getRowId={(p) => String(p.data.id)}
            defaultColDef={{
              editable: false,
              sortable: false,
              resizable: false,
              tooltipComponent: ScheduleCellTooltip,
            }}
            onGridReady={(e) => {
              gridApiRef.current = e.api;
            }}
            onCellMouseOver={onCellMouseOver}
            rowHeight={38}
            headerHeight={22}
            groupHeaderHeight={20}
            suppressCellFocus={true}
            suppressRowClickSelection={true}
            suppressDragLeaveHidesColumns={true}
            domLayout="normal"
            animateRows={false}
            enableCellTextSelection={true}
            tooltipShowDelay={350}
            tooltipHideDelay={100}
          />
        </div>
      </div>
    </div>
  );
}
