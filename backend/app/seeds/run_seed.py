"""Idempotent seed: roles, timesheet codes (Т-12), default admin user."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import CodeCategory
from app.models.timesheet import TimesheetCode
from app.models.user import Role, User, UserRole


def _seed_roles(db: Session) -> dict[str, Role]:
    specs = [
        ("admin", "Администратор", "Полный доступ к системе"),
        ("manager", "Руководитель", "Управление подразделением и графиками"),
        ("operator", "Оператор", "Ввод и правка табеля"),
        ("viewer", "Наблюдатель", "Только просмотр"),
    ]
    by_code: dict[str, Role] = {}
    for code, name, desc in specs:
        row = db.execute(select(Role).where(Role.code == code)).scalar_one_or_none()
        if row is None:
            row = Role(code=code, name=name, description=desc)
            db.add(row)
            db.flush()
        by_code[code] = row
    return by_code


def _seed_timesheet_codes(db: Session) -> None:
    """Базовые коды Т-12: категория, флаги, overlay, цвета."""
    specs: list[dict] = [
        {
            "code": "В",
            "name": "Выходной день",
            "category": CodeCategory.REST,
            "sort_order": 10,
            "replaces_hours": True,
            "can_have_hours_overlay": False,
            "is_overlay": False,
            "counts_as_presence": False,
            "counts_in_timesheet": True,
            "display_color_bg": "#ECEFF1",
            "display_color_text": "#263238",
        },
        {
            "code": "Д",
            "name": "День дороги",
            "category": CodeCategory.ROAD,
            "sort_order": 20,
            "replaces_hours": True,
            "can_have_hours_overlay": False,
            "is_overlay": False,
            "counts_as_presence": False,
            "counts_in_timesheet": True,
            "display_color_bg": "#FFF8E1",
            "display_color_text": "#6D4C41",
        },
        {
            "code": "ОТ",
            "name": "Отпуск",
            "category": CodeCategory.VACATION,
            "sort_order": 30,
            "replaces_hours": True,
            "can_have_hours_overlay": False,
            "is_overlay": False,
            "counts_as_presence": False,
            "counts_in_timesheet": True,
            "display_color_bg": "#E8F5E9",
            "display_color_text": "#1B5E20",
        },
        {
            "code": "Б",
            "name": "Больничный",
            "category": CodeCategory.SICK_LEAVE,
            "sort_order": 40,
            "replaces_hours": True,
            "can_have_hours_overlay": False,
            "is_overlay": False,
            "counts_as_presence": False,
            "counts_in_timesheet": True,
            "display_color_bg": "#FFF3E0",
            "display_color_text": "#E65100",
        },
        {
            "code": "К",
            "name": "Командировка",
            "category": CodeCategory.BUSINESS_TRIP,
            "sort_order": 50,
            "replaces_hours": False,
            "can_have_hours_overlay": True,
            "is_overlay": True,
            "counts_as_presence": True,
            "counts_in_timesheet": True,
            "display_color_bg": "#F3E5F5",
            "display_color_text": "#4A148C",
        },
        {
            "code": "РВД",
            "name": "Работа в выходной день",
            "category": CodeCategory.WEEKEND_WORK,
            "sort_order": 60,
            "replaces_hours": False,
            "can_have_hours_overlay": True,
            "is_overlay": True,
            "counts_as_presence": True,
            "counts_in_timesheet": True,
            "display_color_bg": "#FCE4EC",
            "display_color_text": "#880E4F",
        },
        {
            "code": "С",
            "name": "Сверхурочные",
            "category": CodeCategory.OVERTIME,
            "sort_order": 70,
            "replaces_hours": False,
            "can_have_hours_overlay": True,
            "is_overlay": True,
            "counts_as_presence": True,
            "counts_in_timesheet": True,
            "display_color_bg": "#FFF8E1",
            "display_color_text": "#F57F17",
        },
        {
            "code": "НВ",
            "name": "Неявка без сохранения заработной платы",
            "category": CodeCategory.ABSENCE,
            "sort_order": 80,
            "replaces_hours": True,
            "can_have_hours_overlay": False,
            "is_overlay": False,
            "counts_as_presence": False,
            "counts_in_timesheet": True,
            "display_color_bg": "#FBE9E7",
            "display_color_text": "#BF360C",
        },
        {
            "code": "4",
            "name": "Код 4",
            "category": CodeCategory.CUSTOM,
            "sort_order": 90,
            "replaces_hours": True,
            "can_have_hours_overlay": True,
            "is_overlay": False,
            "counts_as_presence": True,
            "counts_in_timesheet": True,
            "display_color_bg": "#EFEBE9",
            "display_color_text": "#3E2723",
        },
        {
            "code": "5",
            "name": "Код 5",
            "category": CodeCategory.CUSTOM,
            "sort_order": 100,
            "replaces_hours": True,
            "can_have_hours_overlay": True,
            "is_overlay": False,
            "counts_as_presence": True,
            "counts_in_timesheet": True,
            "display_color_bg": "#E0F7FA",
            "display_color_text": "#006064",
        },
        {
            "code": "6",
            "name": "Код 6",
            "category": CodeCategory.CUSTOM,
            "sort_order": 110,
            "replaces_hours": True,
            "can_have_hours_overlay": True,
            "is_overlay": False,
            "counts_as_presence": True,
            "counts_in_timesheet": True,
            "display_color_bg": "#F1F8E9",
            "display_color_text": "#33691E",
        },
    ]
    for spec in specs:
        code = spec["code"]
        row = db.execute(select(TimesheetCode).where(TimesheetCode.code == code)).scalar_one_or_none()
        if row is None:
            row = TimesheetCode(
                code=code,
                name=spec["name"],
                category=spec["category"],
                replaces_hours=spec["replaces_hours"],
                can_have_hours_overlay=spec["can_have_hours_overlay"],
                is_overlay=spec["is_overlay"],
                counts_as_presence=spec["counts_as_presence"],
                counts_in_timesheet=spec["counts_in_timesheet"],
                display_color_bg=spec["display_color_bg"],
                display_color_text=spec["display_color_text"],
                sort_order=spec["sort_order"],
                is_active=True,
            )
            db.add(row)
        else:
            row.name = spec["name"]
            row.category = spec["category"]
            row.replaces_hours = spec["replaces_hours"]
            row.can_have_hours_overlay = spec["can_have_hours_overlay"]
            row.is_overlay = spec["is_overlay"]
            row.counts_as_presence = spec["counts_as_presence"]
            row.counts_in_timesheet = spec["counts_in_timesheet"]
            row.display_color_bg = spec["display_color_bg"]
            row.display_color_text = spec["display_color_text"]
            row.sort_order = spec["sort_order"]


def _seed_admin(db: Session, roles: dict[str, Role]) -> None:
    settings = get_settings()
    email = settings.seed_admin_email.lower().strip()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(settings.seed_admin_password),
            full_name="Администратор",
            is_active=True,
        )
        db.add(user)
        db.flush()
        admin_role = roles["admin"]
        link = db.execute(
            select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == admin_role.id)
        ).scalar_one_or_none()
        if link is None:
            db.add(UserRole(user_id=user.id, role_id=admin_role.id))
    else:
        link = db.execute(
            select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == roles["admin"].id)
        ).scalar_one_or_none()
        if link is None:
            db.add(UserRole(user_id=user.id, role_id=roles["admin"].id))


def run() -> None:
    db = SessionLocal()
    try:
        roles = _seed_roles(db)
        _seed_timesheet_codes(db)
        _seed_admin(db, roles)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
