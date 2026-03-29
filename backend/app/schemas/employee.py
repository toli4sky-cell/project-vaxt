from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EmploymentType, Gender
from app.schemas.common import IdName, SignerBrief


class EmploymentPeriodCreate(BaseModel):
    department_id: int
    position_id: int
    grade: int | None = None
    employment_type: EmploymentType
    workload_rate: Decimal = Field(default=Decimal("1.0"), max_digits=5, decimal_places=2)
    start_date: date
    end_date: date | None = None
    hire_order: str | None = Field(None, max_length=128)
    dismissal_order: str | None = Field(None, max_length=128)
    notes: str | None = None


class EmploymentPeriodUpdate(BaseModel):
    department_id: int | None = None
    position_id: int | None = None
    grade: int | None = None
    employment_type: EmploymentType | None = None
    workload_rate: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    start_date: date | None = None
    end_date: date | None = None
    hire_order: str | None = Field(None, max_length=128)
    dismissal_order: str | None = Field(None, max_length=128)
    notes: str | None = None


class EmploymentPeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department: IdName
    position: IdName
    grade: int | None
    employment_type: EmploymentType
    workload_rate: Decimal
    start_date: date
    end_date: date | None
    hire_order: str | None
    dismissal_order: str | None
    notes: str | None


class EmployeeCreate(BaseModel):
    personnel_number: str = Field(..., max_length=64)
    last_name: str = Field(..., max_length=128)
    first_name: str = Field(..., max_length=128)
    middle_name: str | None = Field(None, max_length=128)
    full_name: str = Field(..., max_length=512)
    gender: Gender | None = None
    birth_date: date | None = None
    passport_number: str | None = Field(None, max_length=64)
    citizenship: str | None = Field(None, max_length=128)
    phone: str | None = Field(None, max_length=64)
    email: str | None = Field(None, max_length=320)
    base_city_id: int | None = None
    cost_center: str | None = Field(None, max_length=128)
    comment: str | None = None
    signer_id: int | None = None
    signer_position: str | None = Field(None, max_length=255)
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    personnel_number: str | None = Field(None, max_length=64)
    last_name: str | None = Field(None, max_length=128)
    first_name: str | None = Field(None, max_length=128)
    middle_name: str | None = Field(None, max_length=128)
    full_name: str | None = Field(None, max_length=512)
    gender: Gender | None = None
    birth_date: date | None = None
    passport_number: str | None = Field(None, max_length=64)
    citizenship: str | None = Field(None, max_length=128)
    phone: str | None = Field(None, max_length=64)
    email: str | None = Field(None, max_length=320)
    base_city_id: int | None = None
    cost_center: str | None = Field(None, max_length=128)
    comment: str | None = None
    signer_id: int | None = None
    signer_position: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class EmployeeSimpleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    personnel_number: str


class EmployeeRead(BaseModel):
    """Карточка и элемент списка: текущие поля из активного трудового периода на сегодня."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    personnel_number: str
    birth_date: date | None
    passport_number: str | None
    citizenship: str | None
    phone: str | None
    email: str | None
    base_city: IdName | None
    signer: SignerBrief | None
    signer_position: str | None
    cost_center: str | None
    comment: str | None
    current_department: IdName | None
    current_position: IdName | None
    current_grade: int | None
    current_employment_type: EmploymentType | None
    employment_periods: list[EmploymentPeriodRead] = []
