from __future__ import annotations

from pydantic import BaseModel

from app.schemas.organization import CityRead, DepartmentRead, PositionRead
from app.schemas.timesheet_code import TimesheetCodeRead


class ReferenceDataResponse(BaseModel):
    """Справочники одним запросом для UI (грид, селекты)."""

    departments: list[DepartmentRead]
    positions: list[PositionRead]
    cities: list[CityRead]
    timesheet_codes: list[TimesheetCodeRead]
