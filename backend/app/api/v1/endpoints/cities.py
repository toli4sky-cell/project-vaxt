from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.organization import City
from app.schemas.common import Paginated
from app.schemas.organization import CityCreate, CityRead, CityUpdate

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("", response_model=Paginated[CityRead])
def list_cities(
    db: DbSession,
    _: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Paginated[CityRead]:
    total = db.execute(select(func.count()).select_from(City)).scalar_one()
    stmt = select(City).order_by(City.name).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return Paginated(items=items, total=total)


@router.get("/{city_id}", response_model=CityRead)
def get_city(db: DbSession, _: CurrentUser, city_id: int) -> City:
    row = db.get(City, city_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


@router.post("", response_model=CityRead, status_code=status.HTTP_201_CREATED)
def create_city(db: DbSession, _: CurrentUser, body: CityCreate) -> City:
    row = City(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{city_id}", response_model=CityRead)
def update_city(db: DbSession, _: CurrentUser, city_id: int, body: CityUpdate) -> City:
    row = db.get(City, city_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{city_id}", status_code=status.HTTP_200_OK)
def delete_city(db: DbSession, _: CurrentUser, city_id: int) -> None:
    row = db.get(City, city_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(row)
    db.commit()
