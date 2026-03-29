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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Direction, GenerationStatus, GenerationType
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.organization import Department
    from app.models.template import WorkTemplate
    from app.models.timesheet import TimesheetCode, TimesheetFactEntry
    from app.models.user import User


class ScheduleGeneration(Base, TimestampMixin):
    __tablename__ = "schedule_generations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"))
    generation_type: Mapped[GenerationType] = mapped_column(
        SQLEnum(
            GenerationType,
            name="generation_type",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ), nullable=False
    )
    based_on_generation_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedule_generations.id", ondelete="SET NULL")
    )
    started_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[GenerationStatus] = mapped_column(
            SQLEnum(
                GenerationStatus,
                name="generation_status",
                values_callable=lambda enum_cls: [e.value for e in enum_cls],
                validate_strings=True,
            ),
        nullable=False,
        default=GenerationStatus.PENDING,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped[Department | None] = relationship()
    started_by: Mapped[User | None] = relationship(foreign_keys=[started_by_id])
    based_on: Mapped[ScheduleGeneration | None] = relationship(
        remote_side="ScheduleGeneration.id",
        back_populates="derived_generations",
        foreign_keys=[based_on_generation_id],
    )
    derived_generations: Mapped[list[ScheduleGeneration]] = relationship(
        back_populates="based_on",
        foreign_keys=[based_on_generation_id],
    )
    plan_entries: Mapped[list[SchedulePlanEntry]] = relationship(
        back_populates="generation", cascade="all, delete-orphan"
    )


class SchedulePlanEntry(Base):
    __tablename__ = "schedule_plan_entries"
    __table_args__ = (
        UniqueConstraint("generation_id", "employee_id", "work_date", name="uq_plan_gen_emp_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    generation_id: Mapped[int] = mapped_column(
        ForeignKey("schedule_generations.id", ondelete="CASCADE"), index=True
    )
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("work_templates.id", ondelete="SET NULL"))
    code_id: Mapped[int | None] = mapped_column(ForeignKey("timesheet_codes.id", ondelete="SET NULL"))
    overlay_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("timesheet_codes.id", ondelete="SET NULL"), nullable=True
    )
    total_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    day_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    night_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    top_display_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bottom_display_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    style_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    derived_direction: Mapped[Direction] = mapped_column(
                SQLEnum(
                    Direction,
                    name="direction",
                    values_callable=lambda enum_cls: [e.value for e in enum_cls],
                    validate_strings=True,
                ), nullable=False, default=Direction.NONE
    )
        
    derived_presence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    generation: Mapped[ScheduleGeneration] = relationship(back_populates="plan_entries")
    employee: Mapped[Employee] = relationship()
    template: Mapped["WorkTemplate | None"] = relationship(
        "WorkTemplate", foreign_keys=[template_id]
    )
    code: Mapped["TimesheetCode | None"] = relationship(
        "TimesheetCode", foreign_keys=[code_id], back_populates="plan_entries"
    )
    overlay_code: Mapped["TimesheetCode | None"] = relationship(
        "TimesheetCode", foreign_keys=[overlay_code_id], back_populates="overlay_plan_entries"
    )
    fact_entries: Mapped[list["TimesheetFactEntry"]] = relationship(
        "TimesheetFactEntry", back_populates="plan_entry"
    )
