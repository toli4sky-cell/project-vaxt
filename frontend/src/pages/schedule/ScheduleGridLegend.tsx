const LEGEND = [
  { label: "Рабочее время", className: "bg-[#dbeafe] border-slate-300" },
  { label: "Выходной", className: "bg-[#ebe8e1] border-slate-300" },
  { label: "Дорога", className: "bg-[#e8eaed] border-slate-300" },
  { label: "Отпуск", className: "bg-[#d5f0dd] border-slate-300" },
  { label: "Больничный", className: "bg-[#ffedd5] border-slate-300" },
  { label: "Командировка", className: "bg-[#ece6ff] border-slate-300" },
  { label: "РВД", className: "bg-[#f8d7da] border-slate-300" },
  { label: "Сверхурочно", className: "bg-[#fef3c7] border-slate-300" },
] as const;

export function ScheduleGridLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-slate-200/80 px-3 py-2 text-[10px] text-slate-600">
      <span className="mr-1 font-medium text-slate-500">Условные обозначения:</span>
      {LEGEND.map((item) => (
        <span key={item.label} className="inline-flex items-center gap-1">
          <span className={`inline-block h-2.5 w-2.5 shrink-0 rounded-sm border ${item.className}`} aria-hidden />
          {item.label}
        </span>
      ))}
    </div>
  );
}
