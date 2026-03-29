from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.employee import Employee, EmployeeEmploymentPeriod
from app.models.organization import City, Department, Position
from app.schemas.common import IdName, SignerBrief
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeSimpleRead,
    EmployeeUpdate,
    EmploymentPeriodCreate,
    EmploymentPeriodRead,
    EmploymentPeriodUpdate,
)
from app.utils.periods import assert_no_overlap, pick_current_interval_index


def _period_to_read(p: EmployeeEmploymentPeriod) -> EmploymentPeriodRead:
    return EmploymentPeriodRead(
        id=p.id,
        department=IdName(id=p.department.id, name=p.department.name),
        position=IdName(id=p.position.id, name=p.position.name),
        grade=p.grade,
        employment_type=p.employment_type,
        workload_rate=p.workload_rate,
        start_date=p.start_date,
        end_date=p.end_date,
        hire_order=p.hire_order,
        dismissal_order=p.dismissal_order,
        notes=p.notes,
    )


def employee_to_read(emp: Employee) -> EmployeeRead:
    periods = sorted(emp.employment_periods, key=lambda x: x.start_date)
    period_reads = [_period_to_read(p) for p in periods]
    intervals = [(p.start_date, p.end_date) for p in periods]
    idx = pick_current_interval_index(intervals)
    cur_dep = cur_pos = None
    cur_grade = None
    cur_et = None
    if idx is not None:
        cp = periods[idx]
        cur_dep = IdName(id=cp.department.id, name=cp.department.name)
        cur_pos = IdName(id=cp.position.id, name=cp.position.name)
        cur_grade = cp.grade
        cur_et = cp.employment_type

    signer_brief = None
    if emp.signer is not None:
        signer_brief = SignerBrief(id=emp.signer.id, full_name=emp.signer.full_name)

    base_city = None
    if emp.base_city is not None:
        base_city = IdName(id=emp.base_city.id, name=emp.base_city.name)

    return EmployeeRead(
        id=emp.id,
        full_name=emp.full_name,
        personnel_number=emp.personnel_number,
        birth_date=emp.birth_date,
        passport_number=emp.passport_number,
        citizenship=emp.citizenship,
        phone=emp.phone,
        email=emp.email,
        base_city=base_city,
        signer=signer_brief,
        signer_position=emp.signer_position,
        cost_center=emp.cost_center,
        comment=emp.comment,
        current_department=cur_dep,
        current_position=cur_pos,
        current_grade=cur_grade,
        current_employment_type=cur_et,
        employment_periods=period_reads,
    )


def _load_employee(db: Session, employee_id: int) -> Employee | None:
    stmt = (
        select(Employee)
        .where(Employee.id == employee_id)
        .options(
            selectinload(Employee.employment_periods).selectinload(EmployeeEmploymentPeriod.department),
            selectinload(Employee.employment_periods).selectinload(EmployeeEmploymentPeriod.position),
            selectinload(Employee.base_city),
            selectinload(Employee.signer),
        )
    )
    return db.execute(stmt).scalar_one_or_none()


def _validate_signer_not_self(employee_id: int | None, signer_id: int | None) -> None:
    if signer_id is not None and employee_id is not None and signer_id == employee_id:
        raise ValueError("signer_id не может совпадать с id сотрудника")


def _validate_employment_periods_overlap(db: Session, employee_id: int) -> None:
    stmt = select(EmployeeEmploymentPeriod).where(EmployeeEmploymentPeriod.employee_id == employee_id)
    rows = list(db.execute(stmt).scalars().all())
    intervals = [(r.start_date, r.end_date) for r in rows]
    assert_no_overlap(intervals)


def get_employee(db: Session, employee_id: int) -> EmployeeRead | None:
    emp = _load_employee(db, employee_id)
    if emp is None:
        return None
    return employee_to_read(emp)


def list_employees(db: Session, *, skip: int = 0, limit: int = 100) -> tuple[list[EmployeeRead], int]:
    count_stmt = select(func.count()).select_from(Employee)
    total = db.execute(count_stmt).scalar_one()
    stmt = (
        select(Employee)
        .order_by(Employee.full_name)
        .offset(skip)
        .limit(limit)
        .options(
            selectinload(Employee.employment_periods).selectinload(EmployeeEmploymentPeriod.department),
            selectinload(Employee.employment_periods).selectinload(EmployeeEmploymentPeriod.position),
            selectinload(Employee.base_city),
            selectinload(Employee.signer),
        )
    )
    rows = list(db.execute(stmt).scalars().all())
    return [employee_to_read(e) for e in rows], total


def list_employees_simple(
    db: Session, *, skip: int = 0, limit: int = 2000, active_only: bool = True
) -> tuple[list[EmployeeSimpleRead], int]:
    """Краткий список для селектов UI."""
    if active_only:
        count_stmt = select(func.count()).select_from(Employee).where(Employee.is_active.is_(True))
        stmt = (
            select(Employee)
            .where(Employee.is_active.is_(True))
            .order_by(Employee.full_name)
            .offset(skip)
            .limit(limit)
        )
    else:
        count_stmt = select(func.count()).select_from(Employee)
        stmt = select(Employee).order_by(Employee.full_name).offset(skip).limit(limit)
    total = db.execute(count_stmt).scalar_one()
    rows = list(db.execute(stmt).scalars().all())
    return [EmployeeSimpleRead.model_validate(e, from_attributes=True) for e in rows], total


def create_employee(db: Session, data: EmployeeCreate) -> EmployeeRead:
    _validate_signer_not_self(None, data.signer_id)
    if data.signer_id is not None and db.get(Employee, data.signer_id) is None:
        raise ValueError("signer_id: сотрудник не найден")
    if data.base_city_id is not None and db.get(City, data.base_city_id) is None:
        raise ValueError("base_city_id: город не найден")
    emp = Employee(
        personnel_number=data.personnel_number.strip(),
        last_name=data.last_name,
        first_name=data.first_name,
        middle_name=data.middle_name,
        full_name=data.full_name,
        gender=data.gender,
        birth_date=data.birth_date,
        passport_number=data.passport_number,
        citizenship=data.citizenship,
        phone=data.phone,
        email=data.email,
        base_city_id=data.base_city_id,
        cost_center=data.cost_center,
        comment=data.comment,
        signer_id=data.signer_id,
        signer_position=data.signer_position,
        is_active=data.is_active,
    )
    db.add(emp)
    db.flush()
    emp = _load_employee(db, emp.id)
    assert emp is not None
    return employee_to_read(emp)


def update_employee(db: Session, employee_id: int, data: EmployeeUpdate) -> EmployeeRead | None:
    emp = db.get(Employee, employee_id)
    if emp is None:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "signer_id" in payload:
        _validate_signer_not_self(employee_id, payload.get("signer_id"))
        sid = payload.get("signer_id")
        if sid is not None and db.get(Employee, sid) is None:
            raise ValueError("signer_id: сотрудник не найден")
    if payload.get("base_city_id") is not None and db.get(City, payload["base_city_id"]) is None:
        raise ValueError("base_city_id: город не найден")
    for k, v in payload.items():
        setattr(emp, k, v)
    db.flush()
    emp = _load_employee(db, employee_id)
    assert emp is not None
    return employee_to_read(emp)


def create_employment_period(db: Session, employee_id: int, data: EmploymentPeriodCreate) -> EmployeeRead:
    emp = db.get(Employee, employee_id)
    if emp is None:
        raise LookupError("employee not found")
    if db.get(Department, data.department_id) is None:
        raise ValueError("department_id: не найдено")
    if db.get(Position, data.position_id) is None:
        raise ValueError("position_id: не найдено")
    ep = EmployeeEmploymentPeriod(
        employee_id=employee_id,
        department_id=data.department_id,
        position_id=data.position_id,
        grade=data.grade,
        employment_type=data.employment_type,
        workload_rate=data.workload_rate,
        start_date=data.start_date,
        end_date=data.end_date,
        hire_order=data.hire_order,
        dismissal_order=data.dismissal_order,
        notes=data.notes,
    )
    db.add(ep)
    db.flush()
    _validate_employment_periods_overlap(db, employee_id)
    emp = _load_employee(db, employee_id)
    assert emp is not None
    return employee_to_read(emp)


def update_employment_period(
    db: Session, employee_id: int, period_id: int, data: EmploymentPeriodUpdate
) -> EmployeeRead:
    ep = db.get(EmployeeEmploymentPeriod, period_id)
    if ep is None or ep.employee_id != employee_id:
        raise LookupError("period not found")
    payload = data.model_dump(exclude_unset=True)
    if "department_id" in payload and payload["department_id"] is not None:
        if db.get(Department, payload["department_id"]) is None:
            raise ValueError("department_id: не найдено")
    if "position_id" in payload and payload["position_id"] is not None:
        if db.get(Position, payload["position_id"]) is None:
            raise ValueError("position_id: не найдено")
    for k, v in payload.items():
        setattr(ep, k, v)
    db.flush()
    _validate_employment_periods_overlap(db, employee_id)
    emp = _load_employee(db, employee_id)
    assert emp is not None
    return employee_to_read(emp)
