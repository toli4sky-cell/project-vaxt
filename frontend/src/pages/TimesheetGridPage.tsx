import { useMemo } from "react";
import { AgGridReact } from "ag-grid-react";
import type { ColDef } from "ag-grid-community";
import { AllCommunityModule, ModuleRegistry } from "ag-grid-community";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";

ModuleRegistry.registerModules([AllCommunityModule]);

type Row = {
  employee: string;
  day1: string;
  day2: string;
  day3: string;
  hours: number;
};

export function TimesheetGridPage() {
  const columnDefs = useMemo<ColDef<Row>[]>(
    () => [
      { field: "employee", headerName: "Сотрудник", flex: 1, minWidth: 160 },
      { field: "day1", headerName: "01", width: 72 },
      { field: "day2", headerName: "02", width: 72 },
      { field: "day3", headerName: "03", width: 72 },
      { field: "hours", headerName: "Часы", width: 88, type: "numericColumn" },
    ],
    [],
  );

  const rowData: Row[] = useMemo(
    () => [
      { employee: "Иванов И.И.", day1: "Я", day2: "Я", day3: "В", hours: 16 },
      { employee: "Петров П.П.", day1: "Н", day2: "Н", day3: "В", hours: 24 },
      { employee: "Сидорова А.К.", day1: "ОТ", day2: "ОТ", day3: "ОТ", hours: 0 },
    ],
    [],
  );

  return (
    <div>
      <h1 className="text-2xl font-semibold text-white">Timesheet Grid</h1>
      <p className="mt-1 text-slate-400">Заглушка AG Grid с тестовыми данными.</p>
      <div className="ag-theme-quartz mt-6" style={{ height: 360, width: "100%" }}>
        <AgGridReact<Row>
          columnDefs={columnDefs}
          rowData={rowData}
          defaultColDef={{ sortable: true, resizable: true }}
          rowHeight={40}
          headerHeight={40}
        />
      </div>
    </div>
  );
}
