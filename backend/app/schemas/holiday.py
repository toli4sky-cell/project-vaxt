from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class HolidayCreate(BaseModel):
    name: str = Field(..., max_length=255)
    holiday_date: date
    city_id: int | None = None
    production_calendar_id: int | None = None


class HolidayUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    holiday_date: date | None = None
    city_id: int | None = None
    production_calendar_id: int | None = None


class HolidayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    holiday_date: date
    city_id: int | None
    production_calendar_id: int | None
    created_at: datetime
    updated_at: datetime
