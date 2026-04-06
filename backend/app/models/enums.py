from __future__ import annotations

import enum


class Gender(str, enum.Enum):
    M = "M"
    F = "F"


class TemplateGender(str, enum.Enum):
    """Ограничение шаблона по полу: мужской, женский, любой."""

    M = "M"
    F = "F"
    ANY = "ANY"


class EmploymentType(str, enum.Enum):
    MAIN = "main"
    PART_TIME = "part_time"


class TemplateType(str, enum.Enum):
    BASE = "base"
    DEPARTMENT_DERIVED = "department_derived"
    EMPLOYEE_DERIVED = "employee_derived"


class GenerationType(str, enum.Enum):
    """Тип / стадия генерации графика."""

    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    REBUILD = "rebuild"


class GenerationStatus(str, enum.Enum):
    """Статус выполнения задачи генерации (pipeline)."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Direction(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    NONE = "none"


class TimesheetSource(str, enum.Enum):
    GENERATION = "generation"
    MANUAL = "manual"
    VACATION = "vacation"
    IMPORT = "import"
    SYNC = "sync"


class ActionType(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    REVERT = "revert"
    BULK_UPDATE = "bulk_update"
    REGENERATE = "regenerate"


class CodeCategory(str, enum.Enum):
    WORK = "work"
    ROAD = "road"
    ABSENCE = "absence"
    VACATION = "vacation"
    BUSINESS_TRIP = "business_trip"
    SICK_LEAVE = "sick_leave"
    WEEKEND_WORK = "weekend_work"
    OVERTIME = "overtime"
    REST = "rest"
    CUSTOM = "custom"


class VacationSource(str, enum.Enum):
    IMPORT = "import"
    MANUAL = "manual"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
