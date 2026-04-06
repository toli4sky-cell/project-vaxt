from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CodeCategory


class TimesheetCodeCreate(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=255)
    category: CodeCategory | None = None
    replaces_hours: bool = False
    can_have_hours_overlay: bool = False
    is_overlay: bool = False
    counts_as_presence: bool = False
    counts_in_timesheet: bool = True
    display_color_bg: str | None = Field(None, max_length=32)
    display_color_text: str | None = Field(None, max_length=32)
    sort_order: int = 0
    is_active: bool = True


class TimesheetCodeUpdate(BaseModel):
    code: str | None = Field(None, max_length=32)
    name: str | None = Field(None, max_length=255)
    category: CodeCategory | None = None
    replaces_hours: bool | None = None
    can_have_hours_overlay: bool | None = None
    is_overlay: bool | None = None
    counts_as_presence: bool | None = None
    counts_in_timesheet: bool | None = None
    display_color_bg: str | None = Field(None, max_length=32)
    display_color_text: str | None = Field(None, max_length=32)
    sort_order: int | None = None
    is_active: bool | None = None


class TimesheetCodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: CodeCategory | None
    replaces_hours: bool
    can_have_hours_overlay: bool
    is_overlay: bool
    counts_as_presence: bool
    counts_in_timesheet: bool
    display_color_bg: str | None
    display_color_text: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
