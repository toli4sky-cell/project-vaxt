from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import VacationSource


class VacationCreate(BaseModel):
    employee_id: int
    vacation_type_id: int
    start_date: date
    end_date: date
    status: str = Field(default="planned", max_length=32)
    comment: str | None = None
    source: VacationSource = VacationSource.IMPORT
    source_file_name: str | None = Field(None, max_length=512)
    days_count: int | None = None


class VacationUpdate(BaseModel):
    employee_id: int | None = None
    vacation_type_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(None, max_length=32)
    comment: str | None = None
    source: VacationSource | None = None
    source_file_name: str | None = Field(None, max_length=512)
    days_count: int | None = None


class VacationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    vacation_type_id: int
    start_date: date
    end_date: date
    status: str
    comment: str | None
    approved_at: datetime | None
    source: VacationSource
    source_file_name: str | None
    days_count: int | None
    created_at: datetime
    updated_at: datetime


class VacationTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
