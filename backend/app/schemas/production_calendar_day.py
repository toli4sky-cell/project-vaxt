from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductionCalendarDayCreate(BaseModel):
    calendar_id: int
    day_date: date
    is_working_day: bool = True
    day_type: str | None = Field(None, max_length=64)
    norm_hours_m: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    norm_hours_f: Decimal | None = Field(None, max_digits=5, decimal_places=2)


class ProductionCalendarDayUpdate(BaseModel):
    day_date: date | None = None
    is_working_day: bool | None = None
    day_type: str | None = Field(None, max_length=64)
    norm_hours_m: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    norm_hours_f: Decimal | None = Field(None, max_digits=5, decimal_places=2)


class ProductionCalendarDayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    calendar_id: int
    day_date: date
    is_working_day: bool
    day_type: str | None
    norm_hours_m: Decimal | None
    norm_hours_f: Decimal | None
    created_at: datetime
