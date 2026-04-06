from __future__ import annotations

import calendar
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.calendar import Holiday
from app.models.employee import Employee, EmployeeEmploymentPeriod
from app.models.enums import CodeCategory, EmploymentType, GenerationStatus, GenerationType
from app.models.organization import Department
from app.models.schedule import ScheduleGeneration, SchedulePlanEntry
from app.models.timesheet import TimesheetFactEntry
from app.schemas.common import IdName
from app.schemas.employee import EmployeeSimpleRead
from app.schemas.presence import PresenceReportRow
from app.schemas.schedule import (
    GridCell,
    GridReferenceMetadata,
    GridRow,
    HolidayMetaItem,
    MonthBoundary,
    ScheduleGridResponse,
)


def _year_date_range(year: int) -> tuple[date, date]:
    return date(year, 1, 1), date(year, 12, 31)


def grid_date_range(year: int, month: int | None) -> tuple[date, date]:
    if month is None:
        return _year_date_range(year)
    if month < 1 or month > 12:
        raise ValueError("month должен быть от 1 до 12")
    last = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)


def iter_dates_in_range(d0: date, d1: date) -> list[date]:
    out: list[date] = []
    d = d0
    while d <= d1:
        out.append(d)
        d += timedelta(days=1)
    return out


def is_working_code_category(cat: CodeCategory | None) -> bool:
    if cat is None:
        return False
    return cat in (
        CodeCategory.WORK,
        CodeCategory.ROAD,
        CodeCategory.BUSINESS_TRIP,
        CodeCategory.WEEKEND_WORK,
        CodeCategory.OVERTIME,
    )


def cell_counts_as_on_shift(main_code: object | None, total_hours: Decimal | None) -> bool:
    """Присутствие «на вахте»: часы > 0 или counts_as_presence + рабочая категория кода."""
    th = total_hours if total_hours is not None else Decimal(0)
    if th > 0:
        return True
    if main_code is None:
        return False
    counts_as_presence = getattr(main_code, "counts_as_presence", False)
    category = getattr(main_code, "category", None)
    if counts_as_presence and is_working_code_category(category):
        return True
    return False


def empty_cell(d: date) -> GridCell:
    return GridCell(
        date=d,
        code=None,
        overlay_code=None,
        total_hours=None,
        day_hours=None,
        night_hours=None,
        top_text=None,
        bottom_text=None,
        style_type=None,
        derived_direction=None,
        derived_presence=False,
        is_manual_override=False,
    )


def cell_from_fact(fact: TimesheetFactEntry) -> GridCell:
    return GridCell(
        date=fact.work_date,
        code=fact.code.code if fact.code else None,
        overlay_code=fact.overlay_code.code if fact.overlay_code else None,
        total_hours=fact.total_hours,
        day_hours=fact.day_hours,
        night_hours=fact.night_hours,
        top_text=fact.top_display_text,
        bottom_text=fact.bottom_display_text,
        style_type=fact.style_type,
        derived_direction=fact.derived_direction.value if fact.derived_direction else None,
        derived_presence=cell_counts_as_on_shift(fact.code, fact.total_hours),
        is_manual_override=fact.is_manual_override,
    )


def cell_from_plan(plan: SchedulePlanEntry) -> GridCell:
    return GridCell(
        date=plan.work_date,
        code=plan.code.code if plan.code else None,
        overlay_code=plan.overlay_code.code if plan.overlay_code else None,
        total_hours=plan.total_hours,
        day_hours=plan.day_hours,
        night_hours=plan.night_hours,
        top_text=plan.top_display_text,
        bottom_text=plan.bottom_display_text,
        style_type=plan.style_type,
        derived_direction=plan.derived_direction.value if plan.derived_direction else None,
        derived_presence=cell_counts_as_on_shift(plan.code, plan.total_hours),
        is_manual_override=False,
    )


def merge_cell(
    d: date,
    fact: TimesheetFactEntry | None,
    plan: SchedulePlanEntry | None,
) -> GridCell:
    if fact is not None and not fact.is_cancelled:
        return cell_from_fact(fact)
    if plan is not None:
        return cell_from_plan(plan)
    return empty_cell(d)


def _select_active_generations(year: int):
    return (
        select(ScheduleGeneration)
        .where(
            ScheduleGeneration.year == year,
            ScheduleGeneration.generation_type == GenerationType.ACTIVE,
            ScheduleGeneration.status == GenerationStatus.COMPLETED,
        )
        .order_by(ScheduleGeneration.started_at.desc())
    )


def find_active_generation_id(db: Session, year: int, department_id: int | None) -> int | None:
    if department_id is not None:
        gen = db.execute(
            _select_active_generations(year).where(ScheduleGeneration.department_id == department_id).limit(1)
        ).scalar_one_or_none()
        if gen is not None:
            return gen.id
    gen = db.execute(
        _select_active_generations(year).where(ScheduleGeneration.department_id.is_(None)).limit(1)
    ).scalar_one_or_none()
    if gen is not None:
        return gen.id
    gen = db.execute(_select_active_generations(year).limit(1)).scalar_one_or_none()
    return gen.id if gen is not None else None


def list_employees_for_grid(
    db: Session,
    range_start: date,
    range_end: date,
    department_id: int | None,
    employee_id: int | None,
) -> list[Employee]:
    overlap = (
        EmployeeEmploymentPeriod.start_date <= range_end,
        or_(
            EmployeeEmploymentPeriod.end_date.is_(None),
            EmployeeEmploymentPeriod.end_date >= range_start,
        ),
    )
    if employee_id is not None:
        emp = db.get(Employee, employee_id)
        if emp is None or not emp.is_active:
            return []
        stmt = (
            select(EmployeeEmploymentPeriod.id)
            .where(
                EmployeeEmploymentPeriod.employee_id == employee_id,
                *overlap,
            )
            .limit(1)
        )
        if db.execute(stmt).first() is None:
            return []
        if department_id is not None:
            stmt2 = (
                select(EmployeeEmploymentPeriod.id)
                .where(
                    EmployeeEmploymentPeriod.employee_id == employee_id,
                    EmployeeEmploymentPeriod.department_id == department_id,
                    *overlap,
                )
                .limit(1)
            )
            if db.execute(stmt2).first() is None:
                return []
        return [emp]

    stmt = (
        select(Employee)
        .join(EmployeeEmploymentPeriod, EmployeeEmploymentPeriod.employee_id == Employee.id)
        .where(Employee.is_active.is_(True), *overlap)
    )
    if department_id is not None:
        stmt = stmt.where(EmployeeEmploymentPeriod.department_id == department_id)
    stmt = stmt.distinct().order_by(Employee.full_name)
    return list(db.execute(stmt).scalars().all())


def load_periods_for_employees_on_date(
    db: Session, employee_ids: list[int], on_date: date
) -> dict[int, EmployeeEmploymentPeriod]:
    if not employee_ids:
        return {}
    stmt = (
        select(EmployeeEmploymentPeriod)
        .where(
            EmployeeEmploymentPeriod.employee_id.in_(employee_ids),
            EmployeeEmploymentPeriod.start_date <= on_date,
            or_(
                EmployeeEmploymentPeriod.end_date.is_(None),
                EmployeeEmploymentPeriod.end_date >= on_date,
            ),
        )
        .options(
            selectinload(EmployeeEmploymentPeriod.department),
            selectinload(EmployeeEmploymentPeriod.position),
        )
    )
    rows = list(db.execute(stmt).scalars().all())
    by_emp: dict[int, EmployeeEmploymentPeriod] = {}
    for p in rows:
        cur = by_emp.get(p.employee_id)
        if cur is None or p.start_date > cur.start_date:
            by_emp[p.employee_id] = p
    return by_emp


def load_facts_map(
    db: Session, employee_ids: list[int], d0: date, d1: date
) -> dict[tuple[int, date], TimesheetFactEntry]:
    if not employee_ids:
        return {}
    stmt = (
        select(TimesheetFactEntry)
        .where(
            TimesheetFactEntry.employee_id.in_(employee_ids),
            TimesheetFactEntry.work_date >= d0,
            TimesheetFactEntry.work_date <= d1,
        )
        .options(
            selectinload(TimesheetFactEntry.code),
            selectinload(TimesheetFactEntry.overlay_code),
        )
    )
    m: dict[tuple[int, date], TimesheetFactEntry] = {}
    for f in db.execute(stmt).scalars().all():
        m[(f.employee_id, f.work_date)] = f
    return m


def load_plans_map(
    db: Session,
    generation_id: int | None,
    employee_ids: list[int],
    d0: date,
    d1: date,
) -> dict[tuple[int, date], SchedulePlanEntry]:
    if not generation_id or not employee_ids:
        return {}
    stmt = (
        select(SchedulePlanEntry)
        .where(
            SchedulePlanEntry.generation_id == generation_id,
            SchedulePlanEntry.employee_id.in_(employee_ids),
            SchedulePlanEntry.work_date >= d0,
            SchedulePlanEntry.work_date <= d1,
        )
        .options(
            selectinload(SchedulePlanEntry.code),
            selectinload(SchedulePlanEntry.overlay_code),
        )
    )
    m: dict[tuple[int, date], SchedulePlanEntry] = {}
    for p in db.execute(stmt).scalars().all():
        m[(p.employee_id, p.work_date)] = p
    return m


def build_reference_metadata(dates: list[date], db: Session) -> GridReferenceMetadata:
    if not dates:
        return GridReferenceMetadata(weekends=[], holidays=[], month_boundaries=[])
    weekends = [d for d in dates if d.weekday() >= 5]
    d0, d1 = dates[0], dates[-1]
    hol_rows = list(
        db.execute(
            select(Holiday).where(Holiday.holiday_date >= d0, Holiday.holiday_date <= d1).order_by(Holiday.holiday_date)
        ).scalars().all()
    )
    holidays = [HolidayMetaItem(holiday_date=h.holiday_date, name=h.name) for h in hol_rows]
    seen: set[tuple[int, int]] = set()
    month_boundaries: list[MonthBoundary] = []
    for d in dates:
        key = (d.year, d.month)
        if key in seen:
            continue
        seen.add(key)
        last_d = calendar.monthrange(d.year, d.month)[1]
        month_boundaries.append(
            MonthBoundary(
                year=d.year,
                month=d.month,
                first_date=date(d.year, d.month, 1),
                last_date=date(d.year, d.month, last_d),
            )
        )
    month_boundaries.sort(key=lambda m: (m.year, m.month))
    return GridReferenceMetadata(weekends=weekends, holidays=holidays, month_boundaries=month_boundaries)


def build_schedule_grid(
    db: Session,
    *,
    year: int,
    month: int | None,
    department_id: int | None,
    employee_id: int | None,
) -> ScheduleGridResponse:
    d0, d1 = grid_date_range(year, month)
    dates = iter_dates_in_range(d0, d1)
    employees = list_employees_for_grid(db, d0, d1, department_id, employee_id)
    ids = [e.id for e in employees]
    facts_map = load_facts_map(db, ids, d0, d1)
    gen_id = find_active_generation_id(db, year, department_id)
    plans_map = load_plans_map(db, gen_id, ids, d0, d1)
    period_by_emp = load_periods_for_employees_on_date(db, ids, dates[0])
    rows: list[GridRow] = []
    for emp in employees:
        ep = period_by_emp.get(emp.id)
        cur_dep = IdName(id=ep.department.id, name=ep.department.name) if ep else None
        cur_pos = IdName(id=ep.position.id, name=ep.position.name) if ep else None
        grade = ep.grade if ep else None
        cells: list[GridCell] = []
        for d in dates:
            fact = facts_map.get((emp.id, d))
            plan = plans_map.get((emp.id, d))
            cells.append(merge_cell(d, fact, plan))
        rows.append(
            GridRow(
                employee_id=emp.id,
                employee_name=emp.full_name,
                personnel_number=emp.personnel_number,
                current_department=cur_dep,
                current_position=cur_pos,
                current_grade=grade,
                cells=cells,
            )
        )
    emps_simple = [EmployeeSimpleRead.model_validate(e, from_attributes=True) for e in employees]
    meta = build_reference_metadata(dates, db)
    return ScheduleGridResponse(employees=emps_simple, dates=dates, rows=rows, reference_metadata=meta)


def build_empty_grid(db: Session, *, year: int, department_id: int) -> ScheduleGridResponse:
    if db.get(Department, department_id) is None:
        raise ValueError("department_id: подразделение не найдено")
    d0, d1 = _year_date_range(year)
    dates = iter_dates_in_range(d0, d1)
    employees = list_employees_for_grid(db, d0, d1, department_id, None)
    ids = [e.id for e in employees]
    period_by_emp = load_periods_for_employees_on_date(db, ids, dates[0])
    rows: list[GridRow] = []
    for emp in employees:
        ep = period_by_emp.get(emp.id)
        cur_dep = IdName(id=ep.department.id, name=ep.department.name) if ep else None
        cur_pos = IdName(id=ep.position.id, name=ep.position.name) if ep else None
        grade = ep.grade if ep else None
        cells = [empty_cell(d) for d in dates]
        rows.append(
            GridRow(
                employee_id=emp.id,
                employee_name=emp.full_name,
                personnel_number=emp.personnel_number,
                current_department=cur_dep,
                current_position=cur_pos,
                current_grade=grade,
                cells=cells,
            )
        )
    emps_simple = [EmployeeSimpleRead.model_validate(e, from_attributes=True) for e in employees]
    meta = build_reference_metadata(dates, db)
    return ScheduleGridResponse(employees=emps_simple, dates=dates, rows=rows, reference_metadata=meta)


def _main_code_for_presence(
    fact: TimesheetFactEntry | None, plan: SchedulePlanEntry | None
) -> object | None:
    if fact is not None and not fact.is_cancelled:
        if fact.overlay_code is not None and getattr(fact.overlay_code, "counts_as_presence", False):
            return fact.overlay_code
        return fact.code
    if plan is not None:
        if plan.overlay_code is not None and getattr(plan.overlay_code, "counts_as_presence", False):
            return plan.overlay_code
        return plan.code
    return None


def _hours_for_presence(
    fact: TimesheetFactEntry | None, plan: SchedulePlanEntry | None
) -> Decimal | None:
    if fact is not None and not fact.is_cancelled:
        return fact.total_hours
    if plan is not None:
        return plan.total_hours
    return None


def build_presence_report(
    db: Session, *, target_date: date, department_id: int | None
) -> list[PresenceReportRow]:
    stmt = (
        select(Employee)
        .join(EmployeeEmploymentPeriod, EmployeeEmploymentPeriod.employee_id == Employee.id)
        .where(
            Employee.is_active.is_(True),
            EmployeeEmploymentPeriod.employment_type == EmploymentType.MAIN,
            EmployeeEmploymentPeriod.start_date <= target_date,
            or_(
                EmployeeEmploymentPeriod.end_date.is_(None),
                EmployeeEmploymentPeriod.end_date >= target_date,
            ),
        )
    )
    if department_id is not None:
        stmt = stmt.where(EmployeeEmploymentPeriod.department_id == department_id)
    stmt = stmt.distinct().order_by(Employee.full_name)
    employees = list(db.execute(stmt).scalars().all())
    if not employees:
        return []
    ids = [e.id for e in employees]
    facts_map = load_facts_map(db, ids, target_date, target_date)
    gen_id = find_active_generation_id(db, target_date.year, department_id)
    plans_map = load_plans_map(db, gen_id, ids, target_date, target_date)
    period_by_emp = load_periods_for_employees_on_date(db, ids, target_date)
    out: list[PresenceReportRow] = []
    for emp in employees:
        fact = facts_map.get((emp.id, target_date))
        plan = plans_map.get((emp.id, target_date))
        main_code = _main_code_for_presence(fact, plan)
        th = _hours_for_presence(fact, plan)
        if not cell_counts_as_on_shift(main_code, th):
            continue
        ep = period_by_emp.get(emp.id)
        if ep is None:
            continue
        cell = merge_cell(target_date, fact, plan)
        out.append(
            PresenceReportRow(
                employee_id=emp.id,
                full_name=emp.full_name,
                personnel_number=emp.personnel_number,
                department=IdName(id=ep.department.id, name=ep.department.name),
                position=IdName(id=ep.position.id, name=ep.position.name),
                current_grade=ep.grade,
                work_date=target_date,
                total_hours=cell.total_hours,
                day_hours=cell.day_hours,
                night_hours=cell.night_hours,
                code=cell.code,
                overlay_code=cell.overlay_code,
            )
        )
    return out
