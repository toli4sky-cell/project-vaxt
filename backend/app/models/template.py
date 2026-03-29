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
from app.models.enums import TemplateGender, TemplateType
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.organization import Department
    from app.models.user import User


class WorkTemplate(Base, TimestampMixin):
    __tablename__ = "work_templates"
    __table_args__ = (UniqueConstraint("code", name="uq_work_template_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[TemplateType] = mapped_column(
        SQLEnum(
            TemplateType,
            name="template_type",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
    )
    parent_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_templates.id", ondelete="SET NULL"), nullable=True
    )
    gender: Mapped[TemplateGender] = mapped_column(
        SQLEnum(
            TemplateGender,
            name="template_gender",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
    )
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"))
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"))
    cycle_length_days: Mapped[int] = mapped_column(Integer, nullable=False)
    watch_length_days: Mapped[int] = mapped_column(Integer, nullable=False)
    rest_length_days: Mapped[int] = mapped_column(Integer, nullable=False)
    road_in_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    road_out_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    default_daily_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent: Mapped[WorkTemplate | None] = relationship(
        remote_side="WorkTemplate.id",
        back_populates="children",
        foreign_keys=[parent_template_id],
    )
    children: Mapped[list[WorkTemplate]] = relationship(
        back_populates="parent",
        foreign_keys=[parent_template_id],
    )
    department: Mapped[Department | None] = relationship(
        "Department", back_populates="work_templates", foreign_keys=[department_id]
    )
    employee: Mapped[Employee | None] = relationship(
        "Employee", back_populates="work_templates", foreign_keys=[employee_id]
    )

    template_days: Mapped[list[WorkTemplateDay]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    rotation_rules: Mapped[list[TemplateRotationRule]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    night_segments: Mapped[list[TemplateNightSegment]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    assignments: Mapped[list[EmployeeTemplateAssignment]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )


class WorkTemplateDay(Base):
    __tablename__ = "work_template_days"
    __table_args__ = (UniqueConstraint("template_id", "day_index", name="uq_template_day_index"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("work_templates.id", ondelete="CASCADE"), index=True)
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    code_id: Mapped[int | None] = mapped_column(ForeignKey("timesheet_codes.id", ondelete="SET NULL"))
    total_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    day_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    night_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    top_display_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bottom_display_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    style_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_night_period: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_road_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    template: Mapped[WorkTemplate] = relationship(back_populates="template_days")
    code: Mapped["TimesheetCode | None"] = relationship(
        "TimesheetCode", back_populates="template_days"
    )


class TemplateRotationRule(Base):
    __tablename__ = "template_rotation_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("work_templates.id", ondelete="CASCADE"), index=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    allowed_arrival_days_json: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    allowed_departure_days_json: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    allow_hour_alignment: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    template: Mapped[WorkTemplate] = relationship(back_populates="rotation_rules")


class TemplateNightSegment(Base):
    __tablename__ = "template_night_segments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("work_templates.id", ondelete="CASCADE"), index=True)
    start_day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    end_day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_night_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    start_day_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    end_night_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    end_day_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    template: Mapped[WorkTemplate] = relationship(back_populates="night_segments")


class EmployeeTemplateAssignment(Base):
    __tablename__ = "employee_template_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("work_templates.id", ondelete="CASCADE"), index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    employee: Mapped[Employee] = relationship()
    template: Mapped[WorkTemplate] = relationship(back_populates="assignments")
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])
