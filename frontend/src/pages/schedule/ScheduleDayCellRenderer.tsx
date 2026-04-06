import type { ICellRendererParams } from "ag-grid-community";

export type ScheduleDayCell = {
  top_text?: string | null;
  overlay_code?: string | null;
  code?: string | null;
  total_hours?: number | string | null;
  style_type?: string | null;
  weekend?: boolean | null;
  holiday?: boolean | null;
};

export type ScheduleGridRow = {
  id: string | number;
  fio: string;
  tabNumber: string;
  department: string;
} & Record<`d${number}`, ScheduleDayCell | null>;

const DEFAULT_BG = "#0b1220";

function isProbablyDark(hexColor: string): boolean {
  const hex = hexColor.replace("#", "").trim();
  if (hex.length !== 3 && hex.length !== 6) return false;
  const normalized =
    hex.length === 3 ? hex.split("").map((c) => c + c).join("") : hex.padEnd(6, "0");
  const r = parseInt(normalized.slice(0, 2), 16);
  const g = parseInt(normalized.slice(2, 4), 16);
  const b = parseInt(normalized.slice(4, 6), 16);
  // Relative luminance approximation.
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return luminance < 160;
}

function resolveStyleTypeBackground(styleType?: string | null): string | null {
  if (!styleType) return null;
  const v = styleType.trim();
  if (!v) return null;

  // If backend returns a usable CSS color value.
  if (v.startsWith("#")) return v;
  if (v.startsWith("rgb(") || v.startsWith("rgba(") || v.startsWith("hsl(") || v.startsWith("hsla(")) {
    return v;
  }

  // Fallback palette (adjust if backend sends other codes).
  const palette: Record<string, string> = {
    A: "#60a5fa",
    B: "#34d399",
    C: "#fbbf24",
    D: "#a78bfa",
    E: "#fb7185",
  };

  return palette[v] ?? "#93c5fd";
}

function resolveCellColors(cell: ScheduleDayCell): { bg: string; fg: string } {
  if (cell.holiday) return { bg: "#ef4444", fg: "#ffffff" };
  if (cell.weekend) return { bg: "#e2e8f0", fg: "#0f172a" };

  const bgFromStyle = resolveStyleTypeBackground(cell.style_type ?? undefined);
  if (bgFromStyle) {
    if (bgFromStyle.startsWith("#") && isProbablyDark(bgFromStyle)) return { bg: bgFromStyle, fg: "#ffffff" };
    return { bg: bgFromStyle, fg: "#0b1220" };
  }

  // No special state: let theme background show through.
  return { bg: DEFAULT_BG, fg: "#e5e7eb" };
}

function formatHours(totalHours: ScheduleDayCell["total_hours"]): string {
  if (totalHours === null || totalHours === undefined) return "";
  if (typeof totalHours === "number") {
    // Keep it compact (e.g. "8" instead of "8.0").
    const s = totalHours.toString();
    return s;
  }
  return String(totalHours);
}

export function ScheduleDayCellRenderer(
  props: ICellRendererParams<ScheduleGridRow, ScheduleDayCell | null>,
) {
  const cell = props.value;
  if (!cell) return <div style={{ height: "100%" }} />;

  const { bg, fg } = resolveCellColors(cell);

  const overlay = cell.overlay_code ?? null;
  const topText = cell.top_text ?? null;
  const code = cell.code ?? null;
  const hoursText = formatHours(cell.total_hours);

  const showSpecialBg = Boolean(cell.holiday || cell.weekend || cell.style_type);

  return (
    <div
      style={{
        height: "100%",
        width: "100%",
        background: showSpecialBg ? bg : undefined,
        color: fg,
        padding: "4px 4px",
        borderRadius: 4,
        boxSizing: "border-box",
      }}
      className="flex flex-col items-center justify-between text-center"
    >
      <div className="flex flex-col items-center justify-start leading-none">
        {overlay ? (
          <div style={{ fontSize: 10, lineHeight: 1.1, opacity: 0.9 }}>{overlay}</div>
        ) : (
          <div style={{ height: 10 }} />
        )}
        {topText ? (
          <div style={{ fontSize: 11, lineHeight: 1.1 }}>{topText}</div>
        ) : (
          <div style={{ height: 11 }} />
        )}
      </div>

      <div style={{ fontSize: 12, fontWeight: 700, lineHeight: 1.1 }}>
        {code ?? ""}
      </div>

      <div style={{ fontSize: 11, lineHeight: 1.1, opacity: 0.9 }}>{hoursText}</div>
    </div>
  );
}

