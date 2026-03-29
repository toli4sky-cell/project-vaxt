from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.timesheet import TimesheetCode
from app.schemas.common import Paginated
from app.schemas.timesheet_code import TimesheetCodeCreate, TimesheetCodeRead, TimesheetCodeUpdate

router = APIRouter(prefix="/timesheet-codes", tags=["timesheet-codes"])


@router.get("", response_model=Paginated[TimesheetCodeRead])
def list_timesheet_codes(
    db: DbSession,
    _: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Paginated[TimesheetCodeRead]:
    total = db.execute(select(func.count()).select_from(TimesheetCode)).scalar_one()
    stmt = (
        select(TimesheetCode)
        .order_by(TimesheetCode.sort_order, TimesheetCode.code)
        .offset(skip)
        .limit(limit)
    )
    items = list(db.execute(stmt).scalars().all())
    return Paginated(items=items, total=total)


@router.get("/{code_id}", response_model=TimesheetCodeRead)
def get_timesheet_code(db: DbSession, _: CurrentUser, code_id: int) -> TimesheetCode:
    row = db.get(TimesheetCode, code_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


@router.post("", response_model=TimesheetCodeRead, status_code=status.HTTP_201_CREATED)
def create_timesheet_code(db: DbSession, _: CurrentUser, body: TimesheetCodeCreate) -> TimesheetCode:
    exists = db.execute(select(func.count()).select_from(TimesheetCode).where(TimesheetCode.code == body.code)).scalar_one()
    if exists:
        raise HTTPException(status_code=400, detail="Код с таким значением уже существует")
    row = TimesheetCode(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{code_id}", response_model=TimesheetCodeRead)
def update_timesheet_code(db: DbSession, _: CurrentUser, code_id: int, body: TimesheetCodeUpdate) -> TimesheetCode:
    row = db.get(TimesheetCode, code_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    payload = body.model_dump(exclude_unset=True)
    if "code" in payload:
        dup = db.execute(
            select(func.count())
            .select_from(TimesheetCode)
            .where(TimesheetCode.code == payload["code"], TimesheetCode.id != code_id)
        ).scalar_one()
        if dup:
            raise HTTPException(status_code=400, detail="Код с таким значением уже существует")
    for k, v in payload.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{code_id}", status_code=status.HTTP_200_OK)
def delete_timesheet_code(db: DbSession, _: CurrentUser, code_id: int) -> None:
    row = db.get(TimesheetCode, code_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(row)
    db.commit()
