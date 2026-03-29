from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.organization import City, Department, Position
from app.models.timesheet import TimesheetCode
from app.schemas.organization import CityRead, DepartmentRead, PositionRead
from app.schemas.reference import ReferenceDataResponse
from app.schemas.timesheet_code import TimesheetCodeRead

router = APIRouter(prefix="/reference-data", tags=["reference-data"])


@router.get("", response_model=ReferenceDataResponse)
def get_reference_data(db: DbSession, _: CurrentUser) -> ReferenceDataResponse:
    departments = list(db.execute(select(Department).order_by(Department.name)).scalars().all())
    positions = list(db.execute(select(Position).order_by(Position.name)).scalars().all())
    cities = list(db.execute(select(City).order_by(City.name)).scalars().all())
    timesheet_codes = list(
        db.execute(
            select(TimesheetCode)
            .where(TimesheetCode.is_active.is_(True))
            .order_by(TimesheetCode.sort_order, TimesheetCode.code)
        ).scalars().all()
    )
    return ReferenceDataResponse(
        departments=[DepartmentRead.model_validate(d, from_attributes=True) for d in departments],
        positions=[PositionRead.model_validate(p, from_attributes=True) for p in positions],
        cities=[CityRead.model_validate(c, from_attributes=True) for c in cities],
        timesheet_codes=[TimesheetCodeRead.model_validate(t, from_attributes=True) for t in timesheet_codes],
    )
