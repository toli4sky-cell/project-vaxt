from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.organization import Department
from app.models.template import (
    EmployeeTemplateAssignment,
    TemplateNightSegment,
    WorkTemplate,
    WorkTemplateDay,
)
from app.schemas.template import (
    EmployeeTemplateAssignmentCreate,
    EmployeeTemplateAssignmentRead,
    EmployeeTemplateAssignmentUpdate,
    WorkTemplateCreate,
    WorkTemplateRead,
    WorkTemplateUpdate,
)
from app.utils.periods import assert_no_overlap


def _validate_template_days_unique(day_indices: list[int]) -> None:
    if len(day_indices) != len(set(day_indices)):
        raise ValueError("day_index в template_days должны быть уникальны в пределах шаблона")


def _validate_employee_template_assignments_overlap(db: Session, employee_id: int) -> None:
    stmt = select(EmployeeTemplateAssignment).where(EmployeeTemplateAssignment.employee_id == employee_id)
    rows = list(db.execute(stmt).scalars().all())
    intervals = [(r.start_date, r.end_date) for r in rows]
    assert_no_overlap(intervals)


def work_template_to_read(t: WorkTemplate) -> WorkTemplateRead:
    from app.schemas.template import TemplateNightSegmentRead, WorkTemplateDayRead

    days = [
        WorkTemplateDayRead.model_validate(d, from_attributes=True) for d in sorted(t.template_days, key=lambda x: x.day_index)
    ]
    segs = [
        TemplateNightSegmentRead.model_validate(s, from_attributes=True) for s in t.night_segments
    ]
    data = WorkTemplateRead.model_validate(t, from_attributes=True)
    return data.model_copy(update={"template_days": days, "night_segments": segs})


def get_work_template(db: Session, template_id: int) -> WorkTemplateRead | None:
    stmt = (
        select(WorkTemplate)
        .where(WorkTemplate.id == template_id)
        .options(
            selectinload(WorkTemplate.template_days),
            selectinload(WorkTemplate.night_segments),
        )
    )
    t = db.execute(stmt).scalar_one_or_none()
    if t is None:
        return None
    return work_template_to_read(t)


def list_work_templates(db: Session, *, skip: int = 0, limit: int = 100) -> tuple[list[WorkTemplateRead], int]:
    total = db.execute(select(func.count()).select_from(WorkTemplate)).scalar_one()
    stmt = (
        select(WorkTemplate)
        .order_by(WorkTemplate.code)
        .offset(skip)
        .limit(limit)
        .options(
            selectinload(WorkTemplate.template_days),
            selectinload(WorkTemplate.night_segments),
        )
    )
    rows = list(db.execute(stmt).scalars().all())
    return [work_template_to_read(t) for t in rows], total


def create_work_template(db: Session, data: WorkTemplateCreate) -> WorkTemplateRead:
    _validate_template_days_unique([d.day_index for d in data.template_days])
    if data.department_id is not None and db.get(Department, data.department_id) is None:
        raise ValueError("department_id: не найдено")
    from app.models.employee import Employee

    if data.employee_id is not None and db.get(Employee, data.employee_id) is None:
        raise ValueError("employee_id: не найден")
    t = WorkTemplate(
        code=data.code.strip(),
        name=data.name,
        template_type=data.template_type,
        parent_template_id=data.parent_template_id,
        gender=data.gender,
        department_id=data.department_id,
        employee_id=data.employee_id,
        cycle_length_days=data.cycle_length_days,
        watch_length_days=data.watch_length_days,
        rest_length_days=data.rest_length_days,
        road_in_days=data.road_in_days,
        road_out_days=data.road_out_days,
        default_daily_hours=data.default_daily_hours,
        is_active=data.is_active,
        version=data.version,
        notes=data.notes,
    )
    db.add(t)
    db.flush()
    for d in data.template_days:
        db.add(
            WorkTemplateDay(
                template_id=t.id,
                day_index=d.day_index,
                code_id=d.code_id,
                total_hours=d.total_hours,
                day_hours=d.day_hours,
                night_hours=d.night_hours,
                top_display_text=d.top_display_text,
                bottom_display_text=d.bottom_display_text,
                style_type=d.style_type,
                is_night_period=d.is_night_period,
                is_road_day=d.is_road_day,
            )
        )
    for s in data.night_segments:
        db.add(
            TemplateNightSegment(
                template_id=t.id,
                start_day_index=s.start_day_index,
                end_day_index=s.end_day_index,
                start_night_hours=s.start_night_hours,
                start_day_hours=s.start_day_hours,
                end_night_hours=s.end_night_hours,
                end_day_hours=s.end_day_hours,
            )
        )
    db.flush()
    stmt = (
        select(WorkTemplate)
        .where(WorkTemplate.id == t.id)
        .options(
            selectinload(WorkTemplate.template_days),
            selectinload(WorkTemplate.night_segments),
        )
    )
    t2 = db.execute(stmt).scalar_one()
    return work_template_to_read(t2)


def update_work_template(db: Session, template_id: int, data: WorkTemplateUpdate) -> WorkTemplateRead | None:
    t = db.get(WorkTemplate, template_id)
    if t is None:
        return None
    payload = data.model_dump(exclude_unset=True)
    if payload.get("department_id") is not None and db.get(Department, payload["department_id"]) is None:
        raise ValueError("department_id: не найдено")
    if payload.get("employee_id") is not None:
        from app.models.employee import Employee

        if db.get(Employee, payload["employee_id"]) is None:
            raise ValueError("employee_id: не найден")
    for k, v in payload.items():
        setattr(t, k, v)
    db.flush()
    stmt = (
        select(WorkTemplate)
        .where(WorkTemplate.id == template_id)
        .options(
            selectinload(WorkTemplate.template_days),
            selectinload(WorkTemplate.night_segments),
        )
    )
    t2 = db.execute(stmt).scalar_one()
    return work_template_to_read(t2)


def delete_work_template(db: Session, template_id: int) -> bool:
    t = db.get(WorkTemplate, template_id)
    if t is None:
        return False
    db.delete(t)
    return True


def create_template_assignment(
    db: Session, data: EmployeeTemplateAssignmentCreate, *, created_by_id: int | None = None
) -> EmployeeTemplateAssignmentRead:
    from app.models.employee import Employee

    if db.get(Employee, data.employee_id) is None:
        raise ValueError("employee_id: не найден")
    if db.get(WorkTemplate, data.template_id) is None:
        raise ValueError("template_id: не найден")
    a = EmployeeTemplateAssignment(
        employee_id=data.employee_id,
        template_id=data.template_id,
        start_date=data.start_date,
        end_date=data.end_date,
        change_reason=data.change_reason,
        created_by_id=created_by_id,
    )
    db.add(a)
    db.flush()
    _validate_employee_template_assignments_overlap(db, data.employee_id)
    db.refresh(a)
    return EmployeeTemplateAssignmentRead.model_validate(a, from_attributes=True)


def update_template_assignment(
    db: Session, assignment_id: int, data: EmployeeTemplateAssignmentUpdate
) -> EmployeeTemplateAssignmentRead | None:
    a = db.get(EmployeeTemplateAssignment, assignment_id)
    if a is None:
        return None
    payload = data.model_dump(exclude_unset=True)
    if payload.get("template_id") is not None and db.get(WorkTemplate, payload["template_id"]) is None:
        raise ValueError("template_id: не найден")
    for k, v in payload.items():
        setattr(a, k, v)
    db.flush()
    _validate_employee_template_assignments_overlap(db, a.employee_id)
    db.refresh(a)
    return EmployeeTemplateAssignmentRead.model_validate(a, from_attributes=True)


def delete_template_assignment(db: Session, assignment_id: int) -> bool:
    a = db.get(EmployeeTemplateAssignment, assignment_id)
    if a is None:
        return False
    db.delete(a)
    return True


def list_template_assignments_for_employee(db: Session, employee_id: int) -> list[EmployeeTemplateAssignmentRead]:
    stmt = (
        select(EmployeeTemplateAssignment)
        .where(EmployeeTemplateAssignment.employee_id == employee_id)
        .order_by(EmployeeTemplateAssignment.start_date.desc())
    )
    rows = list(db.execute(stmt).scalars().all())
    return [EmployeeTemplateAssignmentRead.model_validate(r, from_attributes=True) for r in rows]
