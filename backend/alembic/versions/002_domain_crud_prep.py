"""CRUD prep: code_category extension, overlays, employees enrichment, indexes.

Revision ID: 002_domain_crud_prep
Revises: 001_initial
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_domain_crud_prep"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # vacation_source enum
    vs = postgresql.ENUM("import", "manual", name="vacation_source")
    vs.create(bind, checkfirst=True)
    vs_nt = postgresql.ENUM("import", "manual", name="vacation_source", create_type=False)

    # code_category: add new labels (PG keeps old values until unused)
    for val in (
        "road",
        "business_trip",
        "sick_leave",
        "weekend_work",
        "overtime",
        "rest",
    ):
        op.execute(sa.text(f"ALTER TYPE code_category ADD VALUE IF NOT EXISTS '{val}'"))

    op.add_column("timesheet_codes", sa.Column("is_overlay", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column(
        "schedule_plan_entries",
        sa.Column("overlay_code_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_schedule_plan_entries_overlay_code",
        "schedule_plan_entries",
        "timesheet_codes",
        ["overlay_code_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "timesheet_fact_entries",
        sa.Column("overlay_code_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_timesheet_fact_entries_overlay_code",
        "timesheet_fact_entries",
        "timesheet_codes",
        ["overlay_code_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("employees", sa.Column("phone", sa.String(length=64), nullable=True))
    op.add_column("employees", sa.Column("citizenship", sa.String(length=128), nullable=True))
    op.add_column("employees", sa.Column("cost_center", sa.String(length=128), nullable=True))
    op.add_column("employees", sa.Column("comment", sa.Text(), nullable=True))
    op.add_column("employees", sa.Column("signer_id", sa.Integer(), nullable=True))
    op.add_column("employees", sa.Column("signer_position", sa.String(length=255), nullable=True))
    op.create_foreign_key(
        "fk_employees_signer_id",
        "employees",
        "employees",
        ["signer_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "vacations",
        sa.Column(
            "source",
            vs_nt,
            nullable=False,
            server_default=sa.text("'import'::vacation_source"),
        ),
    )
    op.add_column("vacations", sa.Column("source_file_name", sa.String(length=512), nullable=True))
    op.add_column("vacations", sa.Column("days_count", sa.Integer(), nullable=True))

    op.drop_constraint("uq_cal_day_date", "production_calendar_days", type_="unique")
    op.alter_column(
        "production_calendar_days",
        "calendar_date",
        new_column_name="day_date",
        existing_type=sa.Date(),
        existing_nullable=False,
    )
    op.create_unique_constraint(
        "uq_cal_day_date", "production_calendar_days", ["calendar_id", "day_date"]
    )
    op.execute(sa.text("DROP INDEX IF EXISTS ix_production_calendar_days_calendar_date"))
    op.create_index(
        op.f("ix_production_calendar_days_day_date"),
        "production_calendar_days",
        ["day_date"],
        unique=False,
    )

    op.execute(
        sa.text(
            """
            ALTER TABLE employee_employment_periods
            ALTER COLUMN grade TYPE INTEGER
            USING CASE
                WHEN grade IS NULL OR trim(grade) = '' THEN NULL
                WHEN grade ~ '^[0-9]+$' THEN grade::integer
                ELSE NULL
            END
            """
        )
    )

    op.create_unique_constraint(
        "uq_secondary_main_sec_start",
        "employee_secondary_links",
        ["main_employee_id", "secondary_employee_id", "start_date"],
    )

    op.create_index(
        "ix_emp_periods_emp_dates",
        "employee_employment_periods",
        ["employee_id", "start_date", "end_date"],
        unique=False,
    )
    op.create_index(
        "ix_emp_tpl_assign_emp_dates",
        "employee_template_assignments",
        ["employee_id", "start_date", "end_date"],
        unique=False,
    )
    op.create_index(
        "ix_vacations_emp_dates",
        "vacations",
        ["employee_id", "start_date", "end_date"],
        unique=False,
    )
    op.create_index(
        "ix_fact_work_presence",
        "timesheet_fact_entries",
        ["work_date", "derived_presence"],
        unique=False,
    )
    op.create_index(
        "ix_fact_work_direction",
        "timesheet_fact_entries",
        ["work_date", "derived_direction"],
        unique=False,
    )
    op.create_index(
        "ix_plan_gen_work_date",
        "schedule_plan_entries",
        ["generation_id", "work_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_plan_gen_work_date", table_name="schedule_plan_entries")
    op.drop_index("ix_fact_work_direction", table_name="timesheet_fact_entries")
    op.drop_index("ix_fact_work_presence", table_name="timesheet_fact_entries")
    op.drop_index("ix_vacations_emp_dates", table_name="vacations")
    op.drop_index("ix_emp_tpl_assign_emp_dates", table_name="employee_template_assignments")
    op.drop_index("ix_emp_periods_emp_dates", table_name="employee_employment_periods")

    op.drop_constraint("uq_secondary_main_sec_start", "employee_secondary_links", type_="unique")

    op.execute(
        sa.text(
            """
            ALTER TABLE employee_employment_periods
            ALTER COLUMN grade TYPE VARCHAR(64)
            USING CASE WHEN grade IS NOT NULL THEN grade::text ELSE NULL END
            """
        )
    )

    op.drop_index(op.f("ix_production_calendar_days_day_date"), table_name="production_calendar_days")
    op.drop_constraint("uq_cal_day_date", "production_calendar_days", type_="unique")
    op.alter_column(
        "production_calendar_days",
        "day_date",
        new_column_name="calendar_date",
        existing_type=sa.Date(),
        existing_nullable=False,
    )
    op.create_unique_constraint(
        "uq_cal_day_date", "production_calendar_days", ["calendar_id", "calendar_date"]
    )
    op.create_index(
        op.f("ix_production_calendar_days_calendar_date"),
        "production_calendar_days",
        ["calendar_date"],
        unique=False,
    )

    op.drop_column("vacations", "days_count")
    op.drop_column("vacations", "source_file_name")
    op.drop_column("vacations", "source")

    op.drop_constraint("fk_employees_signer_id", "employees", type_="foreignkey")
    op.drop_column("employees", "signer_position")
    op.drop_column("employees", "signer_id")
    op.drop_column("employees", "comment")
    op.drop_column("employees", "cost_center")
    op.drop_column("employees", "citizenship")
    op.drop_column("employees", "phone")

    op.drop_constraint("fk_timesheet_fact_entries_overlay_code", "timesheet_fact_entries", type_="foreignkey")
    op.drop_column("timesheet_fact_entries", "overlay_code_id")

    op.drop_constraint("fk_schedule_plan_entries_overlay_code", "schedule_plan_entries", type_="foreignkey")
    op.drop_column("schedule_plan_entries", "overlay_code_id")

    op.drop_column("timesheet_codes", "is_overlay")

    bind = op.get_bind()
    postgresql.ENUM(name="vacation_source").drop(bind, checkfirst=True)
