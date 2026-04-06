from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.common import IdName


class PresenceReportRow(BaseModel):
    employee_id: int
    full_name: str
    personnel_number: str
    department: IdName
    position: IdName
    current_grade: int | None
    work_date: date
    total_hours: Decimal | None
    day_hours: Decimal | None
    night_hours: Decimal | None
    code: str | None
    overlay_code: str | None
