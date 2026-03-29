from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.organization import Position
from app.schemas.common import Paginated
from app.schemas.organization import PositionCreate, PositionRead, PositionUpdate

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("", response_model=Paginated[PositionRead])
def list_positions(
    db: DbSession,
    _: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Paginated[PositionRead]:
    total = db.execute(select(func.count()).select_from(Position)).scalar_one()
    stmt = select(Position).order_by(Position.name).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return Paginated(items=items, total=total)


@router.get("/{position_id}", response_model=PositionRead)
def get_position(db: DbSession, _: CurrentUser, position_id: int) -> Position:
    row = db.get(Position, position_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


@router.post("", response_model=PositionRead, status_code=status.HTTP_201_CREATED)
def create_position(db: DbSession, _: CurrentUser, body: PositionCreate) -> Position:
    row = Position(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{position_id}", response_model=PositionRead)
def update_position(db: DbSession, _: CurrentUser, position_id: int, body: PositionUpdate) -> Position:
    row = db.get(Position, position_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{position_id}", status_code=status.HTTP_200_OK)
def delete_position(db: DbSession, _: CurrentUser, position_id: int) -> None:
    row = db.get(Position, position_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(row)
    db.commit()
