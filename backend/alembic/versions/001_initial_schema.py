"""Initial schema: вахты и табель Т-12 (предметная модель).

Заменяет прежний 001_initial_schema (старые enum'ы и employees без истории).
Для существующей БД до рефакторинга: сделайте бэкап, затем пересоздайте схему
или напишите отдельную миграцию переноса данных.

Revision ID: 001_initial
Revises:
Create Date: 2025-03-22

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(bind, name: str, values: tuple[str, ...]) -> postgresql.ENUM:
    e = postgresql.ENUM(*values, name=name)
    e.create(bind, checkfirst=True)
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()

    gender = _enum(bind, "gender", ("M", "F"))
    employment_type = _enum(bind, "employment_type", ("main", "part_time"))
    template_type = _enum(
        bind, "template_type", ("base", "department_derived", "employee_derived")
    )
    template_gender = _enum(bind, "template_gender", ("M", "F", "ANY"))
    generation_type = _enum(bind, "generation_type", ("draft", "approved", "active", "rebuild"))
    generation_status = _enum(bind, "generation_status", ("pending", "running", "completed", "failed"))
    direction = _enum(bind, "direction", ("inbound", "outbound", "none"))
    timesheet_source = _enum(
        bind, "timesheet_source", ("generation", "manual", "vacation", "import", "sync")
    )
    action_type = _enum(
        bind,
        "action_type",
        ("create", "update", "delete", "revert", "bulk_update", "regenerate"),
    )
    code_category = _enum(
        bind, "code_category", ("work", "absence", "vacation", "holiday", "night", "custom")
    )
    job_status = _enum(bind, "job_status", ("queued", "running", "completed", "failed"))

    j = postgresql.JSONB(astext_type=sa.Text())

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_roles_code"), "roles", ["code"], unique=False)

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["departments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_departments_code"), "departments", ["code"], unique=False)

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_positions_code"), "positions", ["code"], unique=False)

    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cities_code"), "cities", ["code"], unique=False)

    op.create_table(
        "timesheet_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", code_category, nullable=True),
        sa.Column("replaces_hours", sa.Boolean(), nullable=False),
        sa.Column("can_have_hours_overlay", sa.Boolean(), nullable=False),
        sa.Column("counts_as_presence", sa.Boolean(), nullable=False),
        sa.Column("counts_in_timesheet", sa.Boolean(), nullable=False),
        sa.Column("display_color_bg", sa.String(length=32), nullable=True),
        sa.Column("display_color_text", sa.String(length=32), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_timesheet_code_value"),
    )
    op.create_index(op.f("ix_timesheet_codes_code"), "timesheet_codes", ["code"], unique=False)

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("personnel_number", sa.String(length=64), nullable=False),
        sa.Column("last_name", sa.String(length=128), nullable=False),
        sa.Column("first_name", sa.String(length=128), nullable=False),
        sa.Column("middle_name", sa.String(length=128), nullable=True),
        sa.Column("full_name", sa.String(length=512), nullable=False),
        sa.Column("gender", gender, nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("passport_series", sa.String(length=32), nullable=True),
        sa.Column("passport_number", sa.String(length=64), nullable=True),
        sa.Column("passport_issued_by", sa.String(length=512), nullable=True),
        sa.Column("passport_issue_date", sa.Date(), nullable=True),
        sa.Column("registration_address", sa.Text(), nullable=True),
        sa.Column("residential_address", sa.Text(), nullable=True),
        sa.Column("base_city_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["base_city_id"], ["cities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("personnel_number"),
    )
    op.create_index(op.f("ix_employees_email"), "employees", ["email"], unique=False)
    op.create_index(op.f("ix_employees_full_name"), "employees", ["full_name"], unique=False)
    op.create_index(op.f("ix_employees_last_name"), "employees", ["last_name"], unique=False)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    op.create_table(
        "user_department_permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("can_read", sa.Boolean(), nullable=False),
        sa.Column("can_write", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "department_id", name="uq_user_department_perm"),
    )
    op.create_index(
        op.f("ix_user_department_permissions_department_id"),
        "user_department_permissions",
        ["department_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_department_permissions_user_id"),
        "user_department_permissions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "employee_employment_periods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("position_id", sa.Integer(), nullable=False),
        sa.Column("grade", sa.String(length=64), nullable=True),
        sa.Column("employment_type", employment_type, nullable=False),
        sa.Column("workload_rate", sa.Numeric(5, 2), server_default=sa.text("1.0"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("hire_order", sa.String(length=128), nullable=True),
        sa.Column("dismissal_order", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_employee_employment_periods_employee_id"),
        "employee_employment_periods",
        ["employee_id"],
        unique=False,
    )

    op.create_table(
        "employee_secondary_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("main_employee_id", sa.Integer(), nullable=False),
        sa.Column("secondary_employee_id", sa.Integer(), nullable=False),
        sa.Column("factor", sa.Numeric(5, 2), server_default=sa.text("0.1"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["main_employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["secondary_employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_employee_secondary_links_main_employee_id"),
        "employee_secondary_links",
        ["main_employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_secondary_links_secondary_employee_id"),
        "employee_secondary_links",
        ["secondary_employee_id"],
        unique=False,
    )

    op.create_table(
        "employee_attribute_changes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("change_type", sa.String(length=64), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("old_value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_employee_attribute_changes_employee_id"),
        "employee_attribute_changes",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_attribute_changes_change_type"),
        "employee_attribute_changes",
        ["change_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_attribute_changes_effective_date"),
        "employee_attribute_changes",
        ["effective_date"],
        unique=False,
    )

    op.create_table(
        "work_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("template_type", template_type, nullable=False),
        sa.Column("parent_template_id", sa.Integer(), nullable=True),
        sa.Column("gender", template_gender, nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("cycle_length_days", sa.Integer(), nullable=False),
        sa.Column("watch_length_days", sa.Integer(), nullable=False),
        sa.Column("rest_length_days", sa.Integer(), nullable=False),
        sa.Column("road_in_days", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("road_out_days", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("default_daily_hours", sa.Numeric(5, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_template_id"], ["work_templates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_work_template_code"),
    )
    op.create_index(op.f("ix_work_templates_code"), "work_templates", ["code"], unique=False)

    op.create_table(
        "work_template_days",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column("code_id", sa.Integer(), nullable=True),
        sa.Column("total_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("day_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("night_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("top_display_text", sa.String(length=255), nullable=True),
        sa.Column("bottom_display_text", sa.String(length=255), nullable=True),
        sa.Column("style_type", sa.String(length=64), nullable=True),
        sa.Column("is_night_period", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_road_day", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["code_id"], ["timesheet_codes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["template_id"], ["work_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "day_index", name="uq_template_day_index"),
    )
    op.create_index(
        op.f("ix_work_template_days_template_id"), "work_template_days", ["template_id"], unique=False
    )

    op.create_table(
        "template_rotation_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("allowed_arrival_days_json", j, nullable=False),
        sa.Column("allowed_departure_days_json", j, nullable=False),
        sa.Column("allow_hour_alignment", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["work_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_template_rotation_rules_template_id"),
        "template_rotation_rules",
        ["template_id"],
        unique=False,
    )

    op.create_table(
        "template_night_segments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("start_day_index", sa.Integer(), nullable=False),
        sa.Column("end_day_index", sa.Integer(), nullable=False),
        sa.Column("start_night_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("start_day_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("end_night_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("end_day_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["work_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_template_night_segments_template_id"),
        "template_night_segments",
        ["template_id"],
        unique=False,
    )

    op.create_table(
        "employee_template_assignments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["work_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_employee_template_assignments_employee_id"),
        "employee_template_assignments",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_template_assignments_template_id"),
        "employee_template_assignments",
        ["template_id"],
        unique=False,
    )

    op.create_table(
        "vacation_types",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_vacation_type_code"),
    )

    op.create_table(
        "production_calendars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "year", name="uq_production_calendar_name_year"),
    )
    op.create_index(op.f("ix_production_calendars_year"), "production_calendars", ["year"], unique=False)

    op.create_table(
        "holidays",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("holiday_date", sa.Date(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.Column("production_calendar_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["production_calendar_id"], ["production_calendars.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_holidays_holiday_date"), "holidays", ["holiday_date"], unique=False)

    op.create_table(
        "production_calendar_days",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("calendar_id", sa.Integer(), nullable=False),
        sa.Column("calendar_date", sa.Date(), nullable=False),
        sa.Column("is_working_day", sa.Boolean(), nullable=False),
        sa.Column("day_type", sa.String(length=64), nullable=True),
        sa.Column("norm_hours_m", sa.Numeric(5, 2), nullable=True),
        sa.Column("norm_hours_f", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["calendar_id"], ["production_calendars.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("calendar_id", "calendar_date", name="uq_cal_day_date"),
    )
    op.create_index(
        op.f("ix_production_calendar_days_calendar_id"),
        "production_calendar_days",
        ["calendar_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_production_calendar_days_calendar_date"),
        "production_calendar_days",
        ["calendar_date"],
        unique=False,
    )

    op.create_table(
        "vacations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("vacation_type_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vacation_type_id"], ["vacation_types.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vacations_employee_id"), "vacations", ["employee_id"], unique=False)
    op.create_index(op.f("ix_vacations_start_date"), "vacations", ["start_date"], unique=False)
    op.create_index(op.f("ix_vacations_end_date"), "vacations", ["end_date"], unique=False)

    op.create_table(
        "schedule_generations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("generation_type", generation_type, nullable=False),
        sa.Column("based_on_generation_id", sa.Integer(), nullable=True),
        sa.Column("started_by_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", generation_status, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["based_on_generation_id"], ["schedule_generations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["started_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_schedule_generations_year"), "schedule_generations", ["year"], unique=False)

    op.create_table(
        "schedule_plan_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("generation_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("code_id", sa.Integer(), nullable=True),
        sa.Column("total_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("day_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("night_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("top_display_text", sa.String(length=255), nullable=True),
        sa.Column("bottom_display_text", sa.String(length=255), nullable=True),
        sa.Column("style_type", sa.String(length=64), nullable=True),
        sa.Column(
            "derived_direction",
            direction,
            nullable=False,
            server_default=sa.text("'none'::direction"),
        ),
        sa.Column("derived_presence", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["code_id"], ["timesheet_codes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generation_id"], ["schedule_generations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["work_templates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("generation_id", "employee_id", "work_date", name="uq_plan_gen_emp_date"),
    )
    op.create_index(
        op.f("ix_schedule_plan_entries_generation_id"),
        "schedule_plan_entries",
        ["generation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_schedule_plan_entries_employee_id"),
        "schedule_plan_entries",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_schedule_plan_entries_work_date"), "schedule_plan_entries", ["work_date"], unique=False
    )

    op.create_table(
        "timesheet_fact_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("plan_entry_id", sa.Integer(), nullable=True),
        sa.Column("code_id", sa.Integer(), nullable=True),
        sa.Column("total_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("day_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("night_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("top_display_text", sa.String(length=255), nullable=True),
        sa.Column("bottom_display_text", sa.String(length=255), nullable=True),
        sa.Column("style_type", sa.String(length=64), nullable=True),
        sa.Column(
            "derived_direction",
            direction,
            nullable=False,
            server_default=sa.text("'none'::direction"),
        ),
        sa.Column("derived_presence", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "source",
            timesheet_source,
            nullable=False,
            server_default=sa.text("'manual'::timesheet_source"),
        ),
        sa.Column("is_manual_override", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("is_cancelled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("changed_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["changed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["code_id"], ["timesheet_codes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_entry_id"], ["schedule_plan_entries.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "work_date", name="uq_fact_employee_date"),
    )
    op.create_index(
        op.f("ix_timesheet_fact_entries_employee_id"),
        "timesheet_fact_entries",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_timesheet_fact_entries_work_date"), "timesheet_fact_entries", ["work_date"], unique=False
    )

    op.create_table(
        "timesheet_change_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("fact_entry_id", sa.Integer(), nullable=True),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("action_type", action_type, nullable=False),
        sa.Column("old_value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_by_id", sa.Integer(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["changed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fact_entry_id"], ["timesheet_fact_entries.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_timesheet_change_log_fact_entry_id"),
        "timesheet_change_log",
        ["fact_entry_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_timesheet_change_log_employee_id"), "timesheet_change_log", ["employee_id"], unique=False
    )
    op.create_index(
        op.f("ix_timesheet_change_log_work_date"), "timesheet_change_log", ["work_date"], unique=False
    )

    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("file_name", sa.String(length=512), nullable=True),
        sa.Column("storage_path", sa.String(length=1024), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "export_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("export_kind", sa.String(length=64), nullable=True),
        sa.Column("result_path", sa.String(length=1024), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("export_jobs")
    op.drop_table("import_jobs")
    op.drop_table("timesheet_change_log")
    op.drop_table("timesheet_fact_entries")
    op.drop_table("schedule_plan_entries")
    op.drop_table("schedule_generations")
    op.drop_table("vacations")
    op.drop_table("production_calendar_days")
    op.drop_table("holidays")
    op.drop_table("production_calendars")
    op.drop_table("vacation_types")
    op.drop_table("employee_template_assignments")
    op.drop_table("template_night_segments")
    op.drop_table("template_rotation_rules")
    op.drop_table("work_template_days")
    op.drop_table("work_templates")
    op.drop_table("employee_attribute_changes")
    op.drop_table("employee_secondary_links")
    op.drop_table("employee_employment_periods")
    op.drop_table("user_department_permissions")
    op.drop_table("user_roles")
    op.drop_table("employees")
    op.drop_table("timesheet_codes")
    op.drop_table("cities")
    op.drop_table("positions")
    op.drop_table("departments")
    op.drop_table("roles")
    op.drop_table("users")

    bind = op.get_bind()
    for name in (
        "job_status",
        "code_category",
        "action_type",
        "timesheet_source",
        "direction",
        "generation_status",
        "generation_type",
        "template_gender",
        "template_type",
        "employment_type",
        "gender",
    ):
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
