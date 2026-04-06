"""Проверка пересечения дат и выбор «текущего» периода."""

from __future__ import annotations

from datetime import date


def date_ranges_overlap(
    start_a: date,
    end_a: date | None,
    start_b: date,
    end_b: date | None,
) -> bool:
    """Два полуоткрытых/закрытых интервала [start, end] пересекаются (end None = бесконечность)."""
    far_future = date(9999, 12, 31)
    ea = end_a if end_a is not None else far_future
    eb = end_b if end_b is not None else far_future
    return start_a <= eb and start_b <= ea


def assert_no_overlap(
    intervals: list[tuple[date, date | None]],
    *,
    exclude_index: int | None = None,
) -> None:
    """Бросает ValueError при пересечении любой пары интервалов."""
    n = len(intervals)
    for i in range(n):
        if exclude_index is not None and i == exclude_index:
            continue
        for j in range(i + 1, n):
            if exclude_index is not None and j == exclude_index:
                continue
            s1, e1 = intervals[i]
            s2, e2 = intervals[j]
            if date_ranges_overlap(s1, e1, s2, e2):
                raise ValueError("Периоды не должны пересекаться")


def pick_current_interval_index(
    intervals: list[tuple[date, date | None]],
    *,
    on: date | None = None,
) -> int | None:
    """Индекс интервала, действующего на дату on (при нескольких — с максимальным start)."""
    on = on or date.today()
    best_i: int | None = None
    best_start: date | None = None
    for i, (start, end) in enumerate(intervals):
        if start > on:
            continue
        if end is not None and on > end:
            continue
        if best_start is None or start > best_start:
            best_start = start
            best_i = i
    return best_i
