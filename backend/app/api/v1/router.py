from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    cities,
    departments,
    employees,
    holidays,
    positions,
    production_calendar_days,
    reference,
    schedule,
    timesheet_codes,
    vacations,
    work_templates,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(reference.router)
api_router.include_router(schedule.router)
api_router.include_router(timesheet_codes.router)
api_router.include_router(departments.router)
api_router.include_router(positions.router)
api_router.include_router(cities.router)
api_router.include_router(employees.router)
api_router.include_router(work_templates.router)
api_router.include_router(work_templates.assignments_router)
api_router.include_router(vacations.router)
api_router.include_router(holidays.router)
api_router.include_router(production_calendar_days.router)
