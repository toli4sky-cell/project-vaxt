from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import EmploymentType, Gender
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import City, Department, Position
    from app.models.user import User


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    personnel_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    gender: Mapped[Gender | None] = mapped_column(
        SQLEnum(
            Gender,
            name="gender",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ), 
        nullable=True)
    

    
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    passport_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    citizenship: Mapped[str | None] = mapped_column(String(128), nullable=True)
    passport_series: Mapped[str | None] = mapped_column(String(32), nullable=True)
    passport_issued_by: Mapped[str | None] = mapped_column(String(512), nullable=True)
    passport_issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    registration_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    residential_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id", ondelete="SET NULL"))
    cost_center: Mapped[str | None] = mapped_column(String(128), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    signer_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"))
    signer_position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    base_city: Mapped[City | None] = relationship(back_populates="employees_base")
    signer: Mapped[Employee | None] = relationship(
        "Employee", remote_side=[id], foreign_keys=[signer_id], back_populates="signing_for"
    )
    signing_for: Mapped[list[Employee]] = relationship(
        "Employee", foreign_keys=[signer_id], back_populates="signer"
    )

    employment_periods: Mapped[list[EmployeeEmploymentPeriod]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    secondary_links_as_main: Mapped[list[EmployeeSecondaryLink]] = relationship(
        foreign_keys="EmployeeSecondaryLink.main_employee_id",
        back_populates="main_employee",
        cascade="all, delete-orphan",
    )
    attribute_changes: Mapped[list[EmployeeAttributeChange]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    fact_entries: Mapped[list["TimesheetFactEntry"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    work_templates: Mapped[list["WorkTemplate"]] = relationship(
        "WorkTemplate", back_populates="employee", foreign_keys="WorkTemplate.employee_id"
    )


class EmployeeEmploymentPeriod(Base):
    __tablename__ = "employee_employment_periods"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), index=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id", ondelete="RESTRICT"), index=True)
    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employment_type: Mapped[EmploymentType] = mapped_column(
        SQLEnum(
            EmploymentType,
            name="employment_type",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ), nullable=False
    )
    
    
    
    workload_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.0"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    hire_order: Mapped[str | None] = mapped_column(String(128), nullable=True)
    dismissal_order: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="employment_periods")
    department: Mapped[Department] = relationship(back_populates="employment_periods")
    position: Mapped[Position] = relationship(back_populates="employment_periods")


class EmployeeSecondaryLink(Base):
    __tablename__ = "employee_secondary_links"
    __table_args__ = (
        UniqueConstraint("main_employee_id", "secondary_employee_id", "start_date", name="uq_secondary_main_sec_start"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    main_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    secondary_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    factor: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.1"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    main_employee: Mapped[Employee] = relationship(
        foreign_keys=[main_employee_id], back_populates="secondary_links_as_main"
    )
    secondary_employee: Mapped[Employee] = relationship(foreign_keys=[secondary_employee_id])


class EmployeeAttributeChange(Base):
    __tablename__ = "employee_attribute_changes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    change_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    old_value_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    new_value_json: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    employee: Mapped[Employee] = relationship(back_populates="attribute_changes")
    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
