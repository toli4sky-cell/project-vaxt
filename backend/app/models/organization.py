from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import UserDepartmentPermission


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"))

    parent: Mapped[Department | None] = relationship(
        remote_side="Department.id", back_populates="children", foreign_keys=[parent_id]
    )
    children: Mapped[list[Department]] = relationship(back_populates="parent")
    user_permissions: Mapped[list[UserDepartmentPermission]] = relationship(
        back_populates="department"
    )
    employment_periods: Mapped[list["EmployeeEmploymentPeriod"]] = relationship(
        back_populates="department"
    )
    work_templates: Mapped[list["WorkTemplate"]] = relationship(
        "WorkTemplate", back_populates="department"
    )


class Position(Base, TimestampMixin):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    employment_periods: Mapped[list["EmployeeEmploymentPeriod"]] = relationship(
        back_populates="position"
    )


class City(Base, TimestampMixin):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    employees_base: Mapped[list["Employee"]] = relationship(back_populates="base_city")
