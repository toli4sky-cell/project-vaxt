from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.calendar import Holiday, ProductionCalendar
from app.models.organization import City
from app.schemas.common import Paginated
from app.schemas.holiday import HolidayCreate, HolidayRead, HolidayUpdate

router = APIRouter(prefix="/holidays", tags=["holidays"])


@router.get("", response_model=Paginated[HolidayRead])
def list_holidays(
    db: DbSession,
    _: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Paginated[HolidayRead]:
    total = db.execute(select(func.count()).select_from(Holiday)).scalar_one()
    stmt = select(Holiday).order_by(Holiday.holiday_date.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return Paginated(items=items, total=total)


@router.get("/{holiday_id}", response_model=HolidayRead)
def get_holiday(db: DbSession, _: CurrentUser, holiday_id: int) -> Holiday:
    row = db.get(Holiday, holiday_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


@router.post("", response_model=HolidayRead, status_code=status.HTTP_201_CREATED)
def create_holiday(db: DbSession, _: CurrentUser, body: HolidayCreate) -> Holiday:
    if body.city_id is not None and db.get(City, body.city_id) is None:
        raise HTTPException(status_code=400, detail="city_id: город не найден")
    if body.production_calendar_id is not None and db.get(ProductionCalendar, body.production_calendar_id) is None:
        raise HTTPException(status_code=400, detail="production_calendar_id: календарь не найден")
    row = Holiday(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{holiday_id}", response_model=HolidayRead)
def update_holiday(db: DbSession, _: CurrentUser, holiday_id: int, body: HolidayUpdate) -> Holiday:
    row = db.get(Holiday, holiday_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    payload = body.model_dump(exclude_unset=True)
    if payload.get("city_id") is not None and db.get(City, payload["city_id"]) is None:
        raise HTTPException(status_code=400, detail="city_id: город не найден")
    if payload.get("production_calendar_id") is not None and db.get(
        ProductionCalendar, payload["production_calendar_id"]
    ) is None:
        raise HTTPException(status_code=400, detail="production_calendar_id: календарь не найден")
    for k, v in payload.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{holiday_id}", status_code=status.HTTP_200_OK)
def delete_holiday(db: DbSession, _: CurrentUser, holiday_id: int) -> None:
    row = db.get(Holiday, holiday_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(row)
    db.commit()
