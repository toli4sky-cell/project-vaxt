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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ActionType, CodeCategory, Direction, TimesheetSource
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.schedule import SchedulePlanEntry
    from app.models.template import WorkTemplateDay
    from app.models.user import User


class TimesheetCode(Base, TimestampMixin):
    __tablename__ = "timesheet_codes"
    __table_args__ = (UniqueConstraint("code", name="uq_timesheet_code_value"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[CodeCategory] = mapped_column(
        SQLEnum(
            CodeCategory,
            name="code_category",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
    )
    replaces_hours: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_have_hours_overlay: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_overlay: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    counts_as_presence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    counts_in_timesheet: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_color_bg: Mapped[str | None] = mapped_column(String(32), nullable=True)
    display_color_text: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    fact_entries: Mapped[list["TimesheetFactEntry"]] = relationship(
        back_populates="code", foreign_keys="TimesheetFactEntry.code_id"
    )
    plan_entries: Mapped[list["SchedulePlanEntry"]] = relationship(
        back_populates="code", foreign_keys="SchedulePlanEntry.code_id"
    )
    overlay_fact_entries: Mapped[list["TimesheetFactEntry"]] = relationship(
        back_populates="overlay_code", foreign_keys="TimesheetFactEntry.overlay_code_id"
    )
    overlay_plan_entries: Mapped[list["SchedulePlanEntry"]] = relationship(
        back_populates="overlay_code", foreign_keys="SchedulePlanEntry.overlay_code_id"
    )
    template_days: Mapped[list["WorkTemplateDay"]] = relationship(
        "WorkTemplateDay", back_populates="code"
    )


class TimesheetFactEntry(Base, TimestampMixin):
    __tablename__ = "timesheet_fact_entries"
    __table_args__ = (UniqueConstraint("employee_id", "work_date", name="uq_fact_employee_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    plan_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedule_plan_entries.id", ondelete="SET NULL"), nullable=True
    )
    code_id: Mapped[int | None] = mapped_column(
        ForeignKey("timesheet_codes.id", ondelete="SET NULL"), nullable=True
    )
    overlay_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("timesheet_codes.id", ondelete="SET NULL"), nullable=True
    )
    total_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    day_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    night_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    top_display_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bottom_display_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    style_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    derived_direction: Mapped[Direction | None] = mapped_column(
        SQLEnum(
            Direction,
            name="direction",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        )
    )
    derived_presence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[TimesheetSource] = mapped_column(
        SQLEnum(
            TimesheetSource,
            name="timesheet_source",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        default=TimesheetSource.MANUAL,
    )
    is_manual_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    employee: Mapped[Employee] = relationship(back_populates="fact_entries")
    plan_entry: Mapped["SchedulePlanEntry | None"] = relationship(
        "SchedulePlanEntry", back_populates="fact_entries"
    )
    code: Mapped[TimesheetCode | None] = relationship(
        back_populates="fact_entries", foreign_keys=[code_id]
    )
    overlay_code: Mapped[TimesheetCode | None] = relationship(
        back_populates="overlay_fact_entries", foreign_keys=[overlay_code_id]
    )
    changed_by: Mapped[User | None] = relationship(foreign_keys=[changed_by_id])

    change_logs: Mapped[list["TimesheetChangeLog"]] = relationship(back_populates="fact_entry")


class TimesheetChangeLog(Base):
    __tablename__ = "timesheet_change_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fact_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("timesheet_fact_entries.id", ondelete="SET NULL"), index=True
    )
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    action_type: Mapped[ActionType] = mapped_column(
    SQLEnum(
                ActionType,
                name="action_type",
                values_callable=lambda enum_cls: [e.value for e in enum_cls],
                validate_strings=True,
            ),
            nullable=False,
        )     
    old_value_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    new_value_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    fact_entry: Mapped[TimesheetFactEntry | None] = relationship(back_populates="change_logs")
    employee: Mapped[Employee] = relationship()
    changed_by: Mapped[User | None] = relationship(foreign_keys=[changed_by_id])
