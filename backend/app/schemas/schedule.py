from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.common import IdName
from app.schemas.employee import EmployeeSimpleRead


class GridCell(BaseModel):
    """Ячейка табеля (факт/план/пусто), выравнивание с Т-12 и Excel."""

    date: date
    code: str | None = None
    overlay_code: str | None = None
    total_hours: Decimal | None = None
    day_hours: Decimal | None = None
    night_hours: Decimal | None = None
    top_text: str | None = None
    bottom_text: str | None = None
    style_type: str | None = None
    derived_direction: str | None = None
    derived_presence: bool = False
    is_manual_override: bool = False


class GridRow(BaseModel):
    employee_id: int
    employee_name: str
    personnel_number: str
    current_department: IdName | None = None
    current_position: IdName | None = None
    current_grade: int | None = None
    cells: list[GridCell]


class HolidayMetaItem(BaseModel):
    holiday_date: date
    name: str


class MonthBoundary(BaseModel):
    year: int
    month: int
    first_date: date
    last_date: date


class GridReferenceMetadata(BaseModel):
    """Календарные подсказки для UI: выходные, праздники, границы месяцев в диапазоне сетки."""

    weekends: list[date]
    holidays: list[HolidayMetaItem]
    month_boundaries: list[MonthBoundary]


class ScheduleGridResponse(BaseModel):
    employees: list[EmployeeSimpleRead]
    dates: list[date]
    rows: list[GridRow]
    reference_metadata: GridReferenceMetadata


# Обратная совместимость с прежним именем
EmptyGridResponse = ScheduleGridResponse
