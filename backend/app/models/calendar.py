from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import City


class Holiday(Base, TimestampMixin):
    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id", ondelete="SET NULL"))
    production_calendar_id: Mapped[int | None] = mapped_column(
        ForeignKey("production_calendars.id", ondelete="SET NULL")
    )

    city: Mapped[City | None] = relationship()
    calendar: Mapped["ProductionCalendar | None"] = relationship(back_populates="holidays")


class ProductionCalendar(Base, TimestampMixin):
    __tablename__ = "production_calendars"
    __table_args__ = (UniqueConstraint("name", "year", name="uq_production_calendar_name_year"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False, index=True)
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id", ondelete="SET NULL"))

    city: Mapped[City | None] = relationship()
    days: Mapped[list[ProductionCalendarDay]] = relationship(
        back_populates="calendar", cascade="all, delete-orphan"
    )
    holidays: Mapped[list[Holiday]] = relationship(back_populates="calendar")


class ProductionCalendarDay(Base):
    __tablename__ = "production_calendar_days"
    __table_args__ = (UniqueConstraint("calendar_id", "day_date", name="uq_cal_day_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    calendar_id: Mapped[int] = mapped_column(
        ForeignKey("production_calendars.id", ondelete="CASCADE"), index=True
    )
    day_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_working_day: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    day_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    norm_hours_m: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    norm_hours_f: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    calendar: Mapped[ProductionCalendar] = relationship(back_populates="days")
