from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api import deps

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import Paginated
from app.schemas.template import (
    EmployeeTemplateAssignmentCreate,
    EmployeeTemplateAssignmentRead,
    EmployeeTemplateAssignmentUpdate,
    WorkTemplateCreate,
    WorkTemplateRead,
    WorkTemplateUpdate,
)
from app.services import template_service

from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter(prefix="/work-templates", tags=["work-templates"])
assignments_router = APIRouter(prefix="/employee-template-assignments", tags=["employee-template-assignments"])


@router.get("", response_model=Paginated[WorkTemplateRead])
def list_work_templates(
    db: DbSession,
    _: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Paginated[WorkTemplateRead]:
    items, total = template_service.list_work_templates(db, skip=skip, limit=limit)
    return Paginated(items=items, total=total)


@router.get("/{template_id}", response_model=WorkTemplateRead)
def get_work_template(db: DbSession, _: CurrentUser, template_id: int) -> WorkTemplateRead:
    row = template_service.get_work_template(db, template_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


@router.post("", response_model=WorkTemplateRead, status_code=status.HTTP_201_CREATED)
def create_work_template(db: DbSession, _: CurrentUser, body: WorkTemplateCreate) -> WorkTemplateRead:
    try:
        out = template_service.create_work_template(db, body)
        db.commit()
        return out
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/{template_id}", response_model=WorkTemplateRead)
def update_work_template(db: DbSession, _: CurrentUser, template_id: int, body: WorkTemplateUpdate) -> WorkTemplateRead:
    try:
        out = template_service.update_work_template(db, template_id, body)
        if out is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        db.commit()
        return out
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{template_id}", status_code=status.HTTP_200_OK)
def delete_work_template(db: DbSession, _: CurrentUser, template_id: int) -> None:
    ok = template_service.delete_work_template(db, template_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.commit()


@assignments_router.get("/by-employee/{employee_id}", response_model=list[EmployeeTemplateAssignmentRead])
def list_assignments_by_employee(db: DbSession, _: CurrentUser, employee_id: int) -> list[EmployeeTemplateAssignmentRead]:
    return template_service.list_template_assignments_for_employee(db, employee_id)


@assignments_router.post("", response_model=EmployeeTemplateAssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(db: DbSession, user: CurrentUser, body: EmployeeTemplateAssignmentCreate) -> EmployeeTemplateAssignmentRead:
    try:
        out = template_service.create_template_assignment(db, body, created_by_id=user.id)
        db.commit()
        return out
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e


@assignments_router.patch("/{assignment_id}", response_model=EmployeeTemplateAssignmentRead)
def update_assignment(
    db: DbSession, _: CurrentUser, assignment_id: int, body: EmployeeTemplateAssignmentUpdate
) -> EmployeeTemplateAssignmentRead:
    try:
        out = template_service.update_template_assignment(db, assignment_id, body)
        if out is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        db.commit()
        return out
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e


@assignments_router.delete("/{assignment_id}", status_code=status.HTTP_200_OK)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(deps.get_current_user),
):
    assignment = db.get(WorkTemplateAssignment, assignment_id)

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(assignment)
    db.commit()

    return {"success": True}
