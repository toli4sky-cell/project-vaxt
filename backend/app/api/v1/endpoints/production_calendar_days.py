from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.models.calendar import ProductionCalendar, ProductionCalendarDay
from app.schemas.common import Paginated
from app.schemas.production_calendar_day import (
    ProductionCalendarDayCreate,
    ProductionCalendarDayRead,
    ProductionCalendarDayUpdate,
)

router = APIRouter(prefix="/production-calendar-days", tags=["production-calendar-days"])


@router.get("", response_model=Paginated[ProductionCalendarDayRead])
def list_production_calendar_days(
    db: DbSession,
    _: CurrentUser,
    calendar_id: int | None = Query(None, description="Фильтр по производственному календарю"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=2000),
) -> Paginated[ProductionCalendarDayRead]:
    base = select(ProductionCalendarDay)
    count_base = select(func.count()).select_from(ProductionCalendarDay)
    if calendar_id is not None:
        base = base.where(ProductionCalendarDay.calendar_id == calendar_id)
        count_base = select(func.count()).select_from(ProductionCalendarDay).where(
            ProductionCalendarDay.calendar_id == calendar_id
        )
    total = db.execute(count_base).scalar_one()
    stmt = base.order_by(ProductionCalendarDay.day_date).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return Paginated(items=items, total=total)


@router.get("/{day_id}", response_model=ProductionCalendarDayRead)
def get_production_calendar_day(db: DbSession, _: CurrentUser, day_id: int) -> ProductionCalendarDay:
    row = db.get(ProductionCalendarDay, day_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


@router.post("", response_model=ProductionCalendarDayRead, status_code=status.HTTP_201_CREATED)
def create_production_calendar_day(db: DbSession, _: CurrentUser, body: ProductionCalendarDayCreate) -> ProductionCalendarDay:
    if db.get(ProductionCalendar, body.calendar_id) is None:
        raise HTTPException(status_code=400, detail="calendar_id: календарь не найден")
    row = ProductionCalendarDay(**body.model_dump())
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="День с такой датой уже есть в этом календаре") from None
    db.refresh(row)
    return row


@router.patch("/{day_id}", response_model=ProductionCalendarDayRead)
def update_production_calendar_day(
    db: DbSession, _: CurrentUser, day_id: int, body: ProductionCalendarDayUpdate
) -> ProductionCalendarDay:
    row = db.get(ProductionCalendarDay, day_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    payload = body.model_dump(exclude_unset=True)
    for k, v in payload.items():
        setattr(row, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Нарушение уникальности (calendar_id, day_date)") from None
    db.refresh(row)
    return row
