"""
CLI-генератор демо-данных для вахтовой системы.

Запуск (из каталога backend, с установленными зависимостями):
  python -m app.seeds.generate_demo_data --year 2026 --employees 300
"""

from __future__ import annotations

import argparse
import calendar
import random
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterable, Sequence

from faker import Faker
from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.employee import (
    Employee,
    EmployeeAttributeChange,
    EmployeeEmploymentPeriod,
    EmployeeSecondaryLink,
)
from app.models.enums import (
    Direction,
    EmploymentType,
    Gender,
    GenerationStatus,
    GenerationType,
    TemplateGender,
    TemplateType,
    TimesheetSource,
    VacationSource,
)
from app.models.organization import City, Department, Position
from app.models.schedule import ScheduleGeneration, SchedulePlanEntry
from app.models.template import (
    EmployeeTemplateAssignment,
    TemplateNightSegment,
    TemplateRotationRule,
    WorkTemplate,
    WorkTemplateDay,
)
from app.models.timesheet import TimesheetCode, TimesheetFactEntry
from app.models.vacation import Vacation, VacationType
from app.services.schedule_service import cell_counts_as_on_shift, iter_dates_in_range

# Единая метка для поиска и безопасного удаления демо-данных.
DEMO_MARKER = "[DEMO_SEED]"


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate demo data for shift / timesheet system.")
    p.add_argument("--year", type=int, required=True, help="Calendar year for schedule generation")
    p.add_argument(
        "--employees",
        type=int,
        default=200,
        help="Number of demo employees to create (default: 200)",
    )
    p.add_argument(
        "--reset-demo",
        action="store_true",
        help=f"Delete previously generated demo records (marked with {DEMO_MARKER} or DEMO-* codes)",
    )
    return p.parse_args(argv)


# --- helpers: reference data -------------------------------------------------


def create_demo_departments(session: Session, fake: Faker) -> list[Department]:
    n = random.randint(5, 8)
    out: list[Department] = []
    for i in range(n):
        d = Department(
            name=f"{fake.company()} ({DEMO_MARKER})",
            code=f"DEMO-DEP-{i + 1:03d}",
        )
        session.add(d)
        out.append(d)
    session.flush()
    return out


def create_demo_positions(session: Session, fake: Faker) -> list[Position]:
    n = random.randint(10, 15)
    out: list[Position] = []
    for i in range(n):
        p = Position(
            name=f"{fake.job()} (demo)",
            code=f"DEMO-POS-{i + 1:03d}",
            description=f"{DEMO_MARKER} {fake.catch_phrase()}",
        )
        session.add(p)
        out.append(p)
    session.flush()
    return out


def create_demo_cities(session: Session, fake: Faker) -> list[City]:
    n = random.randint(10, 20)
    out: list[City] = []
    for i in range(n):
        c = City(
            name=fake.city_name() if hasattr(fake, "city_name") else fake.city(),
            code=f"DEMO-CITY-{i + 1:03d}",
        )
        session.add(c)
        out.append(c)
    session.flush()
    return out


def _load_timesheet_codes(session: Session) -> dict[str, TimesheetCode]:
    rows = list(session.execute(select(TimesheetCode)).scalars().all())
    by_code = {r.code: r for r in rows}
    required = ["В", "Д", "ОТ", "Б", "К", "РВД", "С", "НВ", "4", "5", "6"]
    missing = [c for c in required if c not in by_code]
    if missing:
        raise RuntimeError(
            "В БД отсутствуют справочные коды Т-12: "
            + ", ".join(missing)
            + ". Запустите сначала python -m app.seeds.run_seed"
        )
    return by_code


def _next_personnel_number(session: Session, allocated: set[str]) -> str:
    for _ in range(5000):
        cand = f"{random.randint(100000, 999999):06d}"
        if cand in allocated:
            continue
        exists = session.execute(select(Employee.id).where(Employee.personnel_number == cand)).first()
        if exists is None:
            allocated.add(cand)
            return cand
    raise RuntimeError("Не удалось подобрать уникальный табельный номер")


def create_demo_employees(
    session: Session,
    fake: Faker,
    *,
    cities: list[City],
    count: int,
) -> tuple[list[Employee], list[Employee]]:
    """
    Возвращает (main_employees, part_time_employees).
    Все сотрудники помечены comment=DEMO_MARKER; табельный номер уникален.
    """
    allocated_pn: set[str] = set()
    mains: list[Employee] = []
    parts: list[Employee] = []

    # Доля совместителей ~22–28 %
    part_target = max(1, int(round(count * random.uniform(0.22, 0.28))))
    flags = [True] * part_target + [False] * (count - part_target)
    random.shuffle(flags)

    for i in range(count):
        is_part = flags[i]
        g = random.choice([Gender.M, Gender.F])
        if g == Gender.M:
            last_name = fake.last_name_male()
            first_name = fake.first_name_male()
            middle_name = fake.middle_name_male() if hasattr(fake, "middle_name_male") else None
        else:
            last_name = fake.last_name_female()
            first_name = fake.first_name_female()
            middle_name = fake.middle_name_female() if hasattr(fake, "middle_name_female") else None

        full_name = " ".join(p for p in (last_name, first_name, middle_name) if p)

        emp = Employee(
            personnel_number=_next_personnel_number(session, allocated_pn),
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            full_name=full_name,
            gender=g,
            birth_date=fake.date_of_birth(minimum_age=22, maximum_age=58),
            email=fake.unique.email(),
            phone=fake.phone_number()[:48],
            citizenship="Российская Федерация",
            passport_number=f"{fake.random_int(min=1000, max=9999)} {fake.random_int(min=100000, max=999999)}",
            cost_center=fake.bothify(text="??-####", letters="ABCDEFGHJKLMNPQRSTUVWXYZ")[:128],
            comment=f"{DEMO_MARKER} synthetic employee #{i + 1}",
            base_city_id=random.choice(cities).id,
            is_active=True,
        )
        session.add(emp)
        if is_part:
            parts.append(emp)
        else:
            mains.append(emp)

    session.flush()
    return mains, parts


def create_demo_templates(
    session: Session,
    fake: Faker,
    departments: list[Department],
    codes: dict[str, TimesheetCode],
) -> list[WorkTemplate]:
    """8–12 базовых шаблонов + 2–4 наследника (department_derived)."""
    n_base = random.randint(8, 12)
    bases: list[WorkTemplate] = []

    pattern_codes = ["4", "4", "В", "Д", "5", "6", "ОТ", "Б", "К", "РВД", "С", "НВ"]

    for i in range(n_base):
        gender = random.choice([TemplateGender.ANY, TemplateGender.M, TemplateGender.F])
        if gender == TemplateGender.M:
            default_h = Decimal("11")
        elif gender == TemplateGender.F:
            default_h = Decimal("10")
        else:
            default_h = Decimal("11") if random.random() < 0.5 else Decimal("10")

        cycle = random.choice([14, 21, 28])
        watch = cycle // 2
        rest = cycle - watch
        dept = random.choice(departments)

        tpl = WorkTemplate(
            code=f"DEMO-WT-{i + 1:03d}",
            name=f"Демо-график {fake.word()} {i + 1}",
            template_type=TemplateType.BASE,
            parent_template_id=None,
            gender=gender,
            department_id=dept.id,
            employee_id=None,
            cycle_length_days=cycle,
            watch_length_days=watch,
            rest_length_days=rest,
            road_in_days=random.choice([0, 1, 1]),
            road_out_days=random.choice([0, 1, 1]),
            default_daily_hours=default_h,
            is_active=True,
            version=1,
            notes=f"{DEMO_MARKER} base template",
        )
        session.add(tpl)
        session.flush()

        night_template = random.random() < 0.45
        night_start = random.randint(0, max(0, cycle - 3))

        for di in range(cycle):
            key = pattern_codes[di % len(pattern_codes)]
            tc = codes[key]
            if key in ("В", "ОТ", "Б", "НВ"):
                th = Decimal("0")
            elif key == "Д":
                th = Decimal("0")
            else:
                th = default_h if key in ("4", "5", "6", "К", "РВД", "С") else Decimal("0")

            is_road = key == "Д"
            is_night_cell = night_template and night_start <= di < night_start + 3

            wd = WorkTemplateDay(
                template_id=tpl.id,
                day_index=di,
                code_id=tc.id,
                total_hours=th,
                day_hours=th if not is_night_cell else (th - Decimal("3") if th > Decimal("3") else th),
                night_hours=Decimal("3") if is_night_cell and th > 0 else Decimal("0"),
                top_display_text=fake.word() if random.random() < 0.2 else None,
                bottom_display_text=None,
                style_type=random.choice(["SHIFT_A", "SHIFT_B", "#1e3a5f"]) if th > 0 else None,
                is_night_period=is_night_cell,
                is_road_day=is_road,
            )
            session.add(wd)

        if night_template:
            seg = TemplateNightSegment(
                template_id=tpl.id,
                start_day_index=night_start,
                end_day_index=min(cycle - 1, night_start + 2),
                start_night_hours=Decimal("3"),
                start_day_hours=Decimal("5"),
                end_night_hours=Decimal("3"),
                end_day_hours=Decimal("5"),
            )
            session.add(seg)

        bases.append(tpl)

    session.flush()

    # Потомки (наследники)
    n_children = random.randint(2, 4)
    children: list[WorkTemplate] = []
    parents = random.sample(bases, k=min(n_children, len(bases)))
    for j, parent in enumerate(parents):
        child = WorkTemplate(
            code=f"DEMO-WT-C{j + 1:03d}",
            name=f"{parent.name} (отдел. вариант)",
            template_type=TemplateType.DEPARTMENT_DERIVED,
            parent_template_id=parent.id,
            gender=parent.gender,
            department_id=random.choice(departments).id,
            employee_id=None,
            cycle_length_days=parent.cycle_length_days,
            watch_length_days=parent.watch_length_days,
            rest_length_days=parent.rest_length_days,
            road_in_days=parent.road_in_days,
            road_out_days=parent.road_out_days,
            default_daily_hours=parent.default_daily_hours,
            is_active=True,
            version=1,
            notes=f"{DEMO_MARKER} derived from {parent.code}",
        )
        session.add(child)
        session.flush()

        # Копируем дни родителя с небольшими отличиями
        parent_days = list(
            session.execute(
                select(WorkTemplateDay).where(WorkTemplateDay.template_id == parent.id).order_by(WorkTemplateDay.day_index)
            ).scalars().all()
        )
        for pd in parent_days:
            th = pd.total_hours
            if th is not None and random.random() < 0.08:
                th = max(Decimal("0"), th - Decimal("1"))
            session.add(
                WorkTemplateDay(
                    template_id=child.id,
                    day_index=pd.day_index,
                    code_id=pd.code_id,
                    total_hours=th,
                    day_hours=pd.day_hours,
                    night_hours=pd.night_hours,
                    top_display_text=pd.top_display_text,
                    bottom_display_text=pd.bottom_display_text,
                    style_type=pd.style_type,
                    is_night_period=pd.is_night_period,
                    is_road_day=pd.is_road_day,
                )
            )
        children.append(child)

    session.flush()
    return bases + children


def assign_templates(
    session: Session,
    employees: Iterable[Employee],
    templates: list[WorkTemplate],
    year: int,
) -> None:
    """Одно назначение на сотрудника на год — интервалы не пересекаются."""
    y0, y1 = date(year, 1, 1), date(year, 12, 31)
    base_only = [t for t in templates if t.template_type == TemplateType.BASE]

    for emp in employees:
        cand = [t for t in base_only if t.gender == TemplateGender.ANY or t.gender.value == emp.gender.value]
        if not cand:
            cand = base_only
        tpl = random.choice(cand)
        session.add(
            EmployeeTemplateAssignment(
                employee_id=emp.id,
                template_id=tpl.id,
                start_date=y0,
                end_date=y1,
                change_reason=f"{DEMO_MARKER} seeded assignment for {year}",
                created_by_id=None,
            )
        )
    session.flush()


def _assignment_for_employee_on(
    session: Session, employee_id: int, on_date: date
) -> EmployeeTemplateAssignment | None:
    stmt = (
        select(EmployeeTemplateAssignment)
        .where(
            EmployeeTemplateAssignment.employee_id == employee_id,
            EmployeeTemplateAssignment.start_date <= on_date,
            or_(
                EmployeeTemplateAssignment.end_date.is_(None),
                EmployeeTemplateAssignment.end_date >= on_date,
            ),
        )
        .order_by(EmployeeTemplateAssignment.start_date.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def _vacation_dates_by_employee(
    session: Session, employee_ids: list[int], year: int
) -> dict[tuple[int, date], bool]:
    d0, d1 = date(year, 1, 1), date(year, 12, 31)
    if not employee_ids:
        return {}
    rows = list(
        session.execute(
            select(Vacation).where(
                Vacation.employee_id.in_(employee_ids),
                Vacation.start_date <= d1,
                Vacation.end_date >= d0,
            )
        ).scalars().all()
    )
    out: dict[tuple[int, date], bool] = {}
    for v in rows:
        s = max(v.start_date, d0)
        e = min(v.end_date, d1)
        d = s
        while d <= e:
            out[(v.employee_id, d)] = True
            d += timedelta(days=1)
    return out


def generate_demo_schedule(
    session: Session,
    year: int,
    employees: list[Employee],
    codes: dict[str, TimesheetCode],
) -> ScheduleGeneration:
    """
    Создаёт schedule_generation + plan_entries на весь год.
    Если уже есть «реальная» ACTIVE+COMPLETED генерация без DEMO_MARKER — демо будет APPROVED,
    чтобы не заменять активный график в UI.
    """
    d0, d1 = date(year, 1, 1), date(year, 12, 31)
    days = iter_dates_in_range(d0, d1)

    real_active_id = session.execute(
        select(ScheduleGeneration.id)
        .where(
            ScheduleGeneration.year == year,
            ScheduleGeneration.generation_type == GenerationType.ACTIVE,
            ScheduleGeneration.status == GenerationStatus.COMPLETED,
            or_(ScheduleGeneration.notes.is_(None), ~ScheduleGeneration.notes.contains(DEMO_MARKER)),
        )
        .limit(1)
    ).scalar_one_or_none()

    gen_type = GenerationType.APPROVED if real_active_id is not None else GenerationType.ACTIVE
    now = datetime.now(timezone.utc)
    gen = ScheduleGeneration(
        year=year,
        department_id=None,
        generation_type=gen_type,
        based_on_generation_id=None,
        started_by_id=None,
        started_at=now,
        completed_at=now,
        status=GenerationStatus.COMPLETED,
        notes=f"{DEMO_MARKER} demo schedule year={year}; type={gen_type.value}",
    )
    session.add(gen)
    session.flush()

    emp_ids = [e.id for e in employees]
    vac_set = _vacation_dates_by_employee(session, emp_ids, year)

    # Кэш дней шаблонов: (template_id, day_index) -> WorkTemplateDay
    day_rows = list(session.execute(select(WorkTemplateDay)).scalars().all())
    day_map: dict[tuple[int, int], WorkTemplateDay] = {(r.template_id, r.day_index): r for r in day_rows}

    # Загружаем коды один раз в объектный кэш по id
    code_by_id = {c.id: c for c in session.execute(select(TimesheetCode)).scalars().all()}

    plans: list[SchedulePlanEntry] = []
    for emp in employees:
        asn = _assignment_for_employee_on(session, emp.id, date(year, 1, 15))
        if asn is None:
            continue
        tpl_id = asn.template_id
        tpl = session.get(WorkTemplate, tpl_id)
        if tpl is None:
            continue
        cycle = tpl.cycle_length_days
        for work_date in days:
            if vac_set.get((emp.id, work_date)):
                tc = codes["ОТ"]
                pe = SchedulePlanEntry(
                    generation_id=gen.id,
                    employee_id=emp.id,
                    work_date=work_date,
                    template_id=tpl_id,
                    code_id=tc.id,
                    overlay_code_id=None,
                    total_hours=Decimal("0"),
                    day_hours=Decimal("0"),
                    night_hours=Decimal("0"),
                    top_display_text="Отпуск",
                    bottom_display_text=None,
                    style_type="VACATION",
                    derived_presence=cell_counts_as_on_shift(tc, Decimal("0")),
                )
                plans.append(pe)
                continue

            offset = (work_date - asn.start_date).days
            if offset < 0:
                offset = 0
            di = offset % cycle
            wtd = day_map.get((tpl_id, di))
            if wtd is None:
                continue
            main_code = code_by_id.get(wtd.code_id) if wtd.code_id else None
            th = wtd.total_hours

            overlay_id = None
            if main_code and main_code.can_have_hours_overlay and random.random() < 0.03:
                overlay_id = random.choice([codes["К"].id, codes["РВД"].id, codes["С"].id])

            pe = SchedulePlanEntry(
                generation_id=gen.id,
                employee_id=emp.id,
                work_date=work_date,
                template_id=tpl_id,
                code_id=wtd.code_id,
                overlay_code_id=overlay_id,
                total_hours=th,
                day_hours=wtd.day_hours,
                night_hours=wtd.night_hours,
                top_display_text=wtd.top_display_text,
                bottom_display_text=wtd.bottom_display_text,
                style_type=wtd.style_type,
                derived_presence=cell_counts_as_on_shift(main_code, th),
            )
            plans.append(pe)

    # batch add
    batch = 800
    for i in range(0, len(plans), batch):
        session.add_all(plans[i : i + batch])
        session.flush()

    return gen


def create_demo_vacations(
    session: Session,
    *,
    main_employees: list[Employee],
    year: int,
) -> None:
    """Отпуска для части штатных сотрудников (EmploymentType.main — не совместители)."""
    vt = session.execute(select(VacationType).where(VacationType.code == "DEMO-OT")).scalar_one_or_none()
    if vt is None:
        vt = VacationType(
            code="DEMO-OT",
            name=f"Демо — ежегодный ({DEMO_MARKER})",
            description=f"{DEMO_MARKER} generated vacation type",
        )
        session.add(vt)
        session.flush()

    pool = main_employees[:]
    random.shuffle(pool)
    n_v = max(5, len(pool) // 10)
    max_doy = 366 if calendar.isleap(year) else 365
    for emp in pool[:n_v]:
        length = random.randint(7, 16)
        start_doy = random.randint(1, max_doy - length)
        start = date(year, 1, 1) + timedelta(days=start_doy - 1)
        end = start + timedelta(days=length - 1)
        session.add(
            Vacation(
                employee_id=emp.id,
                vacation_type_id=vt.id,
                start_date=start,
                end_date=end,
                status="planned",
                comment=f"{DEMO_MARKER} vacation",
                source="manual",
                days_count=length,
            )
        )
    session.flush()


def create_demo_facts(
    session: Session,
    *,
    year: int,
    employees: list[Employee],
    codes: dict[str, TimesheetCode],
) -> None:
    """Факты с ручным override для части сотрудников (по плану этого года)."""
    d0, d1 = date(year, 1, 1), date(year, 12, 31)
    targets = [e for e in employees if random.random() < 0.28]
    if not targets:
        return

    # active generation: предпочитаем демо-генерацию этого года
    gen_id = session.execute(
        select(ScheduleGeneration.id)
        .where(
            ScheduleGeneration.year == year,
            ScheduleGeneration.notes.contains(DEMO_MARKER),
            ScheduleGeneration.status == GenerationStatus.COMPLETED,
        )
        .order_by(ScheduleGeneration.started_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if gen_id is None:
        return

    max_doy = 366 if calendar.isleap(year) else 365
    for emp in targets:
        n_days = random.randint(4, 14)
        day_indexes = random.sample(range(max_doy), k=min(n_days, max_doy))

        for day_index in day_indexes:
            wd = date(year, 1, 1) + timedelta(days=day_index)
            if wd < d0 or wd > d1:
                continue
            plan = session.execute(
                select(SchedulePlanEntry).where(
                    SchedulePlanEntry.generation_id == gen_id,
                    SchedulePlanEntry.employee_id == emp.id,
                    SchedulePlanEntry.work_date == wd,
                )
            ).scalar_one_or_none()
            if plan is None:
                continue

            alt = random.choice([codes["НВ"], codes["Б"], codes["6"], codes["РВД"]])
            th = Decimal("8") if alt.code in ("6", "РВД") else Decimal("0")
            existing = session.execute(
                select(TimesheetFactEntry).where(
                    TimesheetFactEntry.employee_id == emp.id,
                    TimesheetFactEntry.work_date == wd,
                )
            ).scalar_one_or_none()
            if existing is not None:
                existing.plan_entry_id = plan.id
                existing.code_id = alt.id
                existing.total_hours = th
                existing.day_hours = th
                existing.night_hours = Decimal("0")
                existing.top_display_text = "корр."
                existing.style_type = "MANUAL_FIX"
                existing.derived_presence = cell_counts_as_on_shift(alt, th)
                existing.derived_direction = Direction.NONE
                existing.source = TimesheetSource.MANUAL
                existing.is_manual_override = True
                existing.override_reason = f"{DEMO_MARKER} manual deviation"
                existing.comment = f"{DEMO_MARKER} fact override"
            else:
                session.add(
                    TimesheetFactEntry(
                        employee_id=emp.id,
                        work_date=wd,
                        plan_entry_id=plan.id,
                        code_id=alt.id,
                        overlay_code_id=None,
                        total_hours=th,
                        day_hours=th,
                        night_hours=Decimal("0"),
                        top_display_text="корр.",
                        bottom_display_text=None,
                        style_type="MANUAL_FIX",
                        derived_direction=Direction.NONE,
                        derived_presence=cell_counts_as_on_shift(alt, th),
                        source=TimesheetSource.MANUAL,
                        is_manual_override=True,
                        override_reason=f"{DEMO_MARKER} manual deviation",
                        comment=f"{DEMO_MARKER} fact override",
                        is_cancelled=False,
                        changed_by_id=None,
                    )
                )
    session.flush()


def _employment_periods_for_demo(
    session: Session,
    *,
    departments: list[Department],
    positions: list[Position],
    mains: list[Employee],
    parts: list[Employee],
    year: int,
) -> None:
    """Непересекающиеся периоды: у каждого сотрудника один длинный интервал."""
    y0 = date(year, 1, 1)
    long_start = y0 - timedelta(days=random.randint(300, 600))

    for emp in mains:
        session.add(
            EmployeeEmploymentPeriod(
                employee_id=emp.id,
                department_id=random.choice(departments).id,
                position_id=random.choice(positions).id,
                grade=random.choice([None, 13, 14, 15, 16]),
                employment_type=EmploymentType.MAIN,
                workload_rate=Decimal("1.0"),
                start_date=long_start,
                end_date=None,
                hire_order=f"DEMO-ORD-{emp.id}",
                notes=f"{DEMO_MARKER} main employment",
            )
        )

    # Совместители: частичная занятость, период внутри окна года (тоже один интервал — без пересечений)
    for emp in parts:
        start = date(year, random.choice([1, 2, 3]), 1)
        end = date(year, 11, 30)
        session.add(
            EmployeeEmploymentPeriod(
                employee_id=emp.id,
                department_id=random.choice(departments).id,
                position_id=random.choice(positions).id,
                grade=None,
                employment_type=EmploymentType.PART_TIME,
                workload_rate=Decimal(random.choice(["0.25", "0.5", "0.75"])),
                start_date=start,
                end_date=end,
                hire_order=f"DEMO-PT-{emp.id}",
                notes=f"{DEMO_MARKER} part-time",
            )
        )
    session.flush()


def _department_id_for_employee(session: Session, employee_id: int) -> int | None:
    row = session.execute(
        select(EmployeeEmploymentPeriod.department_id)
        .where(EmployeeEmploymentPeriod.employee_id == employee_id)
        .order_by(EmployeeEmploymentPeriod.start_date.desc())
        .limit(1)
    ).first()
    return int(row[0]) if row else None


def _secondary_links_for_demo(session: Session, mains: list[Employee], parts: list[Employee]) -> None:
    """Связь совместителя с основным сотрудником (предпочтительно в том же подразделении)."""
    if not mains or not parts:
        return
    n_links = min(len(parts), max(3, len(parts) // 5))
    random.shuffle(parts)
    for sec in parts[:n_links]:
        sec_dept = _department_id_for_employee(session, sec.id)
        pool = [m for m in mains if _department_id_for_employee(session, m.id) == sec_dept]
        main = random.choice(pool) if pool else random.choice(mains)
        session.add(
            EmployeeSecondaryLink(
                main_employee_id=main.id,
                secondary_employee_id=sec.id,
                factor=Decimal(random.choice(["0.1", "0.2", "0.25", "0.3"])),
                start_date=date.today().replace(month=1, day=1),
                end_date=None,
            )
        )
    session.flush()


# --- reset -------------------------------------------------------------------


def reset_demo_data(session: Session) -> None:
    """Удаляет объекты, помеченные DEMO_MARKER или с префиксом кода DEMO-."""
    demo_emp_ids = list(
        session.execute(select(Employee.id).where(Employee.comment.contains(DEMO_MARKER))).scalars().all()
    )
    demo_gen_ids = list(
        session.execute(
            select(ScheduleGeneration.id).where(ScheduleGeneration.notes.contains(DEMO_MARKER))
        ).scalars().all()
    )

    if demo_gen_ids:
        session.execute(delete(SchedulePlanEntry).where(SchedulePlanEntry.generation_id.in_(demo_gen_ids)))
        session.execute(delete(ScheduleGeneration).where(ScheduleGeneration.id.in_(demo_gen_ids)))

    if demo_emp_ids:
        session.execute(
            delete(TimesheetFactEntry).where(TimesheetFactEntry.employee_id.in_(demo_emp_ids)),
        )
        session.execute(delete(Vacation).where(Vacation.employee_id.in_(demo_emp_ids)))
        session.execute(
            delete(EmployeeSecondaryLink).where(
                or_(
                    EmployeeSecondaryLink.main_employee_id.in_(demo_emp_ids),
                    EmployeeSecondaryLink.secondary_employee_id.in_(demo_emp_ids),
                )
            ),
        )
        session.execute(delete(EmployeeAttributeChange).where(EmployeeAttributeChange.employee_id.in_(demo_emp_ids)))
        session.execute(
            delete(EmployeeTemplateAssignment).where(EmployeeTemplateAssignment.employee_id.in_(demo_emp_ids)),
        )
        session.execute(delete(EmployeeEmploymentPeriod).where(EmployeeEmploymentPeriod.employee_id.in_(demo_emp_ids)))
        session.execute(delete(Employee).where(Employee.id.in_(demo_emp_ids)))

    demo_tpl_ids = list(
        session.execute(
            select(WorkTemplate.id).where(
                or_(WorkTemplate.notes.contains(DEMO_MARKER), WorkTemplate.code.startswith("DEMO-WT"))
            )
        ).scalars().all()
    )
    if demo_tpl_ids:
        session.execute(delete(TemplateNightSegment).where(TemplateNightSegment.template_id.in_(demo_tpl_ids)))
        session.execute(delete(WorkTemplateDay).where(WorkTemplateDay.template_id.in_(demo_tpl_ids)))
        session.execute(delete(TemplateRotationRule).where(TemplateRotationRule.template_id.in_(demo_tpl_ids)))
        # Снимаем ссылки parent/child внутри демо-набора, чтобы один DELETE не упёрся в FK.
        session.execute(
            update(WorkTemplate)
            .where(WorkTemplate.id.in_(demo_tpl_ids))
            .values(parent_template_id=None)
        )
        session.execute(delete(WorkTemplate).where(WorkTemplate.id.in_(demo_tpl_ids)))

    session.execute(delete(VacationType).where(VacationType.code == "DEMO-OT"))
    session.execute(delete(Department).where(Department.code.startswith("DEMO-")))
    session.execute(delete(Position).where(Position.code.startswith("DEMO-")))
    session.execute(delete(City).where(City.code.startswith("DEMO-")))
    session.flush()


# --- main --------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    fake = Faker("ru_RU")

    session = SessionLocal()
    try:
        if args.reset_demo:
            reset_demo_data(session)
            session.commit()

        codes = _load_timesheet_codes(session)

        departments = create_demo_departments(session, fake)
        positions = create_demo_positions(session, fake)
        cities = create_demo_cities(session, fake)
        mains, parts = create_demo_employees(session, fake, cities=cities, count=args.employees)
        all_employees = mains + parts

        _employment_periods_for_demo(
            session, departments=departments, positions=positions, mains=mains, parts=parts, year=args.year
        )
        _secondary_links_for_demo(session, mains, parts)

        templates = create_demo_templates(session, fake, departments, codes)
        assign_templates(session, all_employees, templates, args.year)

        # Важно: сначала тип отпуска и сами отпуска до генерации плана — план подставит ОТ на эти дни
        create_demo_vacations(session, main_employees=mains, year=args.year)

        generate_demo_schedule(session, args.year, all_employees, codes)
        create_demo_facts(session, year=args.year, employees=all_employees, codes=codes)

        session.commit()
        print(
            f"OK: demo data generated for year={args.year}, employees={len(all_employees)}, "
            f"demo marker={DEMO_MARKER!r}"
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main(sys.argv[1:])
