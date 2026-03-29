from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import Paginated
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeSimpleRead,
    EmployeeUpdate,
    EmploymentPeriodCreate,
    EmploymentPeriodUpdate,
)
from app.services import employee_service

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/simple", response_model=Paginated[EmployeeSimpleRead])
def list_employees_simple(
    db: DbSession,
    _: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(2000, ge=1, le=10000),
    active_only: bool = Query(True, description="Только активные сотрудники"),
) -> Paginated[EmployeeSimpleRead]:
    items, total = employee_service.list_employees_simple(db, skip=skip, limit=limit, active_only=active_only)
    return Paginated(items=items, total=total)


@router.get("", response_model=Paginated[EmployeeRead])
def list_employees(
    db: DbSession,
    _: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Paginated[EmployeeRead]:
    items, total = employee_service.list_employees(db, skip=skip, limit=limit)
    return Paginated(items=items, total=total)


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(db: DbSession, _: CurrentUser, employee_id: int) -> EmployeeRead:
    row = employee_service.get_employee(db, employee_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(db: DbSession, _: CurrentUser, body: EmployeeCreate) -> EmployeeRead:
    try:
        out = employee_service.create_employee(db, body)
        db.commit()
        return out
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Нарушение уникальности (например, табельный номер)") from None


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(db: DbSession, _: CurrentUser, employee_id: int, body: EmployeeUpdate) -> EmployeeRead:
    try:
        out = employee_service.update_employee(db, employee_id, body)
        if out is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        db.commit()
        return out
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Нарушение уникальности (например, табельный номер)") from None


@router.post("/{employee_id}/employment-periods", response_model=EmployeeRead)
def create_employment_period(
    db: DbSession, _: CurrentUser, employee_id: int, body: EmploymentPeriodCreate
) -> EmployeeRead:
    try:
        out = employee_service.create_employment_period(db, employee_id, body)
        db.commit()
        return out
    except LookupError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from None
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/{employee_id}/employment-periods/{period_id}", response_model=EmployeeRead)
def update_employment_period(
    db: DbSession,
    _: CurrentUser,
    employee_id: int,
    period_id: int,
    body: EmploymentPeriodUpdate,
) -> EmployeeRead:
    try:
        out = employee_service.update_employment_period(db, employee_id, period_id, body)
        db.commit()
        return out
    except LookupError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from None
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
