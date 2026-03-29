from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.organization import Department
from app.schemas.common import Paginated
from app.schemas.organization import DepartmentCreate, DepartmentRead, DepartmentUpdate

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=Paginated[DepartmentRead])
def list_departments(
    db: DbSession,
    _: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Paginated[DepartmentRead]:
    total = db.execute(select(func.count()).select_from(Department)).scalar_one()
    stmt = select(Department).order_by(Department.name).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return Paginated(items=items, total=total)


@router.get("/{department_id}", response_model=DepartmentRead)
def get_department(db: DbSession, _: CurrentUser, department_id: int) -> Department:
    row = db.get(Department, department_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(db: DbSession, _: CurrentUser, body: DepartmentCreate) -> Department:
    row = Department(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{department_id}", response_model=DepartmentRead)
def update_department(db: DbSession, _: CurrentUser, department_id: int, body: DepartmentUpdate) -> Department:
    row = db.get(Department, department_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{department_id}", status_code=status.HTTP_200_OK)
def delete_department(db: DbSession, _: CurrentUser, department_id: int) -> None:
    row = db.get(Department, department_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(row)
    db.commit()
