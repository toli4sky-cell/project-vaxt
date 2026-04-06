from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TemplateGender, TemplateType


class WorkTemplateDayIn(BaseModel):
    day_index: int
    code_id: int | None = None
    total_hours: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    day_hours: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    night_hours: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    top_display_text: str | None = Field(None, max_length=255)
    bottom_display_text: str | None = Field(None, max_length=255)
    style_type: str | None = Field(None, max_length=64)
    is_night_period: bool = False
    is_road_day: bool = False


class WorkTemplateDayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    day_index: int
    code_id: int | None
    total_hours: Decimal | None
    day_hours: Decimal | None
    night_hours: Decimal | None
    top_display_text: str | None
    bottom_display_text: str | None
    style_type: str | None
    is_night_period: bool
    is_road_day: bool
    created_at: datetime


class TemplateNightSegmentIn(BaseModel):
    start_day_index: int
    end_day_index: int
    start_night_hours: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    start_day_hours: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    end_night_hours: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    end_day_hours: Decimal | None = Field(None, max_digits=5, decimal_places=2)


class TemplateNightSegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    start_day_index: int
    end_day_index: int
    start_night_hours: Decimal | None
    start_day_hours: Decimal | None
    end_night_hours: Decimal | None
    end_day_hours: Decimal | None
    created_at: datetime


class WorkTemplateCreate(BaseModel):
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    template_type: TemplateType
    parent_template_id: int | None = None
    gender: TemplateGender
    department_id: int | None = None
    employee_id: int | None = None
    cycle_length_days: int
    watch_length_days: int
    rest_length_days: int
    road_in_days: int = 1
    road_out_days: int = 1
    default_daily_hours: Decimal = Field(..., max_digits=5, decimal_places=2)
    is_active: bool = True
    version: int = 1
    notes: str | None = None
    template_days: list[WorkTemplateDayIn]
    night_segments: list[TemplateNightSegmentIn] = []


class WorkTemplateUpdate(BaseModel):
    code: str | None = Field(None, max_length=64)
    name: str | None = Field(None, max_length=255)
    template_type: TemplateType | None = None
    parent_template_id: int | None = None
    gender: TemplateGender | None = None
    department_id: int | None = None
    employee_id: int | None = None
    cycle_length_days: int | None = None
    watch_length_days: int | None = None
    rest_length_days: int | None = None
    road_in_days: int | None = None
    road_out_days: int | None = None
    default_daily_hours: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    is_active: bool | None = None
    version: int | None = None
    notes: str | None = None


class WorkTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    template_type: TemplateType
    parent_template_id: int | None
    gender: TemplateGender
    department_id: int | None
    employee_id: int | None
    cycle_length_days: int
    watch_length_days: int
    rest_length_days: int
    road_in_days: int
    road_out_days: int
    default_daily_hours: Decimal
    is_active: bool
    version: int
    notes: str | None
    created_at: datetime
    updated_at: datetime
    template_days: list[WorkTemplateDayRead] = []
    night_segments: list[TemplateNightSegmentRead] = []


class EmployeeTemplateAssignmentCreate(BaseModel):
    employee_id: int
    template_id: int
    start_date: date
    end_date: date | None = None
    change_reason: str | None = None


class EmployeeTemplateAssignmentUpdate(BaseModel):
    template_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    change_reason: str | None = None


class EmployeeTemplateAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    template_id: int
    start_date: date
    end_date: date | None
    change_reason: str | None
    created_by_id: int | None
    created_at: datetime

