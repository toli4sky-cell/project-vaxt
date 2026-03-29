from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    name: str = Field(..., max_length=255)
    code: str | None = Field(None, max_length=64)
    parent_id: int | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    code: str | None = Field(None, max_length=64)
    parent_id: int | None = None


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str | None
    parent_id: int | None
    created_at: datetime
    updated_at: datetime


class PositionCreate(BaseModel):
    name: str = Field(..., max_length=255)
    code: str | None = Field(None, max_length=64)
    description: str | None = None


class PositionUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    code: str | None = Field(None, max_length=64)
    description: str | None = None


class PositionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime


class CityCreate(BaseModel):
    name: str = Field(..., max_length=255)
    code: str | None = Field(None, max_length=64)


class CityUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    code: str | None = Field(None, max_length=64)


class CityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str | None
    created_at: datetime
    updated_at: datetime
