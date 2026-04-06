from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.employee import Employee
from app.models.vacation import Vacation, VacationType
from app.schemas.vacation import VacationCreate, VacationRead, VacationUpdate

router = APIRouter(prefix="/vacations", tags=["vacations"])


@router.get("", response_model=list[VacationRead])
def list_vacations(
    db: DbSession,
    _: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[Vacation]:
    stmt = select(Vacation).order_by(Vacation.start_date.desc()).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


@router.get("/{vacation_id}", response_model=VacationRead)
def get_vacation(db: DbSession, _: CurrentUser, vacation_id: int) -> Vacation:
    row = db.get(Vacation, vacation_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


@router.post("", response_model=VacationRead, status_code=status.HTTP_201_CREATED)
def create_vacation(db: DbSession, _: CurrentUser, body: VacationCreate) -> Vacation:
    if db.get(Employee, body.employee_id) is None:
        raise HTTPException(status_code=400, detail="employee_id: сотрудник не найден")
    if db.get(VacationType, body.vacation_type_id) is None:
        raise HTTPException(status_code=400, detail="vacation_type_id: тип не найден")
    row = Vacation(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{vacation_id}", response_model=VacationRead)
def update_vacation(db: DbSession, _: CurrentUser, vacation_id: int, body: VacationUpdate) -> Vacation:
    row = db.get(Vacation, vacation_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    payload = body.model_dump(exclude_unset=True)
    if payload.get("employee_id") is not None and db.get(Employee, payload["employee_id"]) is None:
        raise HTTPException(status_code=400, detail="employee_id: сотрудник не найден")
    if payload.get("vacation_type_id") is not None and db.get(VacationType, payload["vacation_type_id"]) is None:
        raise HTTPException(status_code=400, detail="vacation_type_id: тип не найден")
    for k, v in payload.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{vacation_id}", status_code=status.HTTP_200_OK)
def delete_vacation(db: DbSession, _: CurrentUser, vacation_id: int) -> None:
    row = db.get(Vacation, vacation_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(row)
    db.commit()
