from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.presence import PresenceReportRow
from app.schemas.schedule import ScheduleGridResponse
from app.services import schedule_service

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.get("/grid", response_model=ScheduleGridResponse)
def get_schedule_grid(
    db: DbSession,
    _: CurrentUser,
    year: int = Query(..., ge=2000, le=2100, description="Календарный год"),
    month: int | None = Query(
        None,
        ge=1,
        le=12,
        description="Месяц (1–12); если не указан — весь год",
    ),
    department_id: int | None = Query(None, ge=1, description="Фильтр по подразделению в периоде трудоустройства"),
    employee_id: int | None = Query(None, ge=1, description="Один сотрудник (опционально)"),
) -> ScheduleGridResponse:
    try:
        return schedule_service.build_schedule_grid(
            db,
            year=year,
            month=month,
            department_id=department_id,
            employee_id=employee_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/presence-report", response_model=list[PresenceReportRow])
def get_presence_report(
    db: DbSession,
    _: CurrentUser,
    target_date: date = Query(..., description="Дата проверки присутствия"),
    department_id: int | None = Query(None, ge=1, description="Ограничить подразделением (текущий период на дату)"),
) -> list[PresenceReportRow]:
    return schedule_service.build_presence_report(db, target_date=target_date, department_id=department_id)


@router.get("/empty-grid", response_model=ScheduleGridResponse)
def get_empty_grid(
    db: DbSession,
    _: CurrentUser,
    year: int = Query(..., ge=2000, le=2100, description="Календарный год"),
    department_id: int = Query(..., ge=1, description="Подразделение (фильтр по периодам трудоустройства"),
) -> ScheduleGridResponse:
    try:
        return schedule_service.build_empty_grid(db, year=year, department_id=department_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
