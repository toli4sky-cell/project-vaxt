from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import VacationSource
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class VacationType(Base, TimestampMixin):
    __tablename__ = "vacation_types"
    __table_args__ = (UniqueConstraint("code", name="uq_vacation_type_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    vacations: Mapped[list["Vacation"]] = relationship(back_populates="vacation_type")


class Vacation(Base, TimestampMixin):
    __tablename__ = "vacations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    vacation_type_id: Mapped[int] = mapped_column(ForeignKey("vacation_types.id", ondelete="RESTRICT"))
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="planned", nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[VacationSource] = mapped_column(
        SQLEnum(
            VacationSource,
            name="vacation_source",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
    )
    source_file_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    days_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    employee: Mapped[Employee] = relationship()
    vacation_type: Mapped[VacationType] = relationship(back_populates="vacations")
