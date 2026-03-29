import { apiFetch } from "@/shared/api/client";

export async function getScheduleGrid(year: number): Promise<any> {
  // GET /api/v1/schedule/grid?year=YEAR
  const res = await apiFetch(`/api/v1/schedule/grid?year=${encodeURIComponent(String(year))}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? "Не удалось загрузить schedule grid");
  }
  return res.json();
}

