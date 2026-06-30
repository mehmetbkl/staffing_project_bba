# dashboard/data/employees.py
#
# Mitarbeiterliste mit wöchentlichem Schichtplan.
#
# Primärquelle ist jetzt die Datenbank (staff.employees + staff.shifts).
# Die untenstehende Liste EMPLOYEES dient als Fallback (Demo-Modus), falls die
# DB nicht erreichbar oder leer ist – analog zu den anderen Services.
#
# Schichtzeiten als ("HH:MM", "HH:MM") oder None wenn kein Dienst.
# weekday-Schlüssel: "Mon".."Sun".

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_WEEKDAY_NUM_TO_KEY = {
    1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun",
}
_WEEKDAY_KEYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ── Fallback-Stammdaten (Demo-Modus) ─────────────────────────────────────────

EMPLOYEES = [
    {
        "id":   "AK",
        "name": "Anna K.",
        "role": "Kassierer",
        "shifts": {
            "Mon": ("08:00", "14:00"),
            "Tue": ("08:00", "14:00"),
            "Wed": ("12:00", "20:00"),
            "Thu": None,
            "Fri": ("08:00", "14:00"),
            "Sat": ("10:00", "16:00"),
            "Sun": None,
        },
    },
    {
        "id":   "TM",
        "name": "Thomas M.",
        "role": "Abteilungsleiter",
        "shifts": {
            "Mon": ("08:00", "16:00"),
            "Tue": ("08:00", "16:00"),
            "Wed": ("08:00", "16:00"),
            "Thu": ("08:00", "16:00"),
            "Fri": ("08:00", "16:00"),
            "Sat": None,
            "Sun": None,
        },
    },
    {
        "id":   "SB",
        "name": "Sara B.",
        "role": "Kassierer",
        "shifts": {
            "Mon": ("10:00", "18:00"),
            "Tue": None,
            "Wed": ("10:00", "18:00"),
            "Thu": ("10:00", "18:00"),
            "Fri": ("10:00", "18:00"),
            "Sat": ("08:00", "14:00"),
            "Sun": None,
        },
    },
    {
        "id":   "MR",
        "name": "Max R.",
        "role": "Lagerist",
        "shifts": {
            "Mon": ("06:00", "14:00"),
            "Tue": ("06:00", "14:00"),
            "Wed": None,
            "Thu": ("06:00", "14:00"),
            "Fri": ("06:00", "14:00"),
            "Sat": ("06:00", "12:00"),
            "Sun": None,
        },
    },
    {
        "id":   "LW",
        "name": "Lisa W.",
        "role": "Kassierer",
        "shifts": {
            "Mon": None,
            "Tue": ("14:00", "20:00"),
            "Wed": ("14:00", "20:00"),
            "Thu": ("14:00", "20:00"),
            "Fri": ("14:00", "20:00"),
            "Sat": ("12:00", "20:00"),
            "Sun": None,
        },
    },
    {
        "id":   "KS",
        "name": "Klaus S.",
        "role": "Abteilungsleiter",
        "shifts": {
            "Mon": None,
            "Tue": None,
            "Wed": ("12:00", "20:00"),
            "Thu": ("12:00", "20:00"),
            "Fri": ("12:00", "20:00"),
            "Sat": ("10:00", "18:00"),
            "Sun": None,
        },
    },
]


# ── DB-Quelle (staff.employees + staff.shifts) ───────────────────────────────

# Cache, damit nicht jede Seite neu lädt. reset_employees_cache() leert ihn.
_CACHE: dict[str, object] = {"employees": None, "source": "demo"}


def _load_from_db() -> list[dict] | None:
    """
    Lädt Mitarbeiter inkl. Wochenschichten aus staff.employees/staff.shifts.
    Gibt None zurück, wenn DB nicht erreichbar oder leer.
    """
    try:
        from services.db import read_sql
    except Exception:  # pragma: no cover - Service nicht verfügbar
        return None

    df = read_sql("""
        SELECT e.id, e.name, e.role,
               s.weekday, s.shift_start, s.shift_end
        FROM staff.employees e
        LEFT JOIN staff.shifts s ON s.employee_id = e.id
        WHERE e.active
        ORDER BY e.id, s.weekday
    """)
    if df is None or df.empty:
        return None

    by_id: dict[str, dict] = {}
    for row in df.itertuples(index=False):
        emp = by_id.setdefault(row.id, {
            "id": row.id, "name": row.name, "role": row.role,
            "shifts": {k: None for k in _WEEKDAY_KEYS},
        })
        if row.weekday is not None and row.shift_start is not None:
            key = _WEEKDAY_NUM_TO_KEY.get(int(row.weekday))
            if key:
                emp["shifts"][key] = (
                    row.shift_start.strftime("%H:%M"),
                    row.shift_end.strftime("%H:%M"),
                )
    return list(by_id.values()) or None


def get_employees() -> list[dict]:
    """
    Beste verfügbare Mitarbeiterliste: DB (staff.*) → sonst statischer Fallback.
    Ergebnis wird gecacht.
    """
    if _CACHE["employees"] is not None:
        return _CACHE["employees"]  # type: ignore[return-value]

    db = _load_from_db()
    if db:
        _CACHE["employees"] = db
        _CACHE["source"] = "db"
        logger.info("Personaldaten: staff-Schema (DB) – %d Mitarbeiter", len(db))
    else:
        _CACHE["employees"] = EMPLOYEES
        _CACHE["source"] = "demo"
        logger.info("Personaldaten: Fallback employees.py (DB leer/nicht erreichbar)")
    return _CACHE["employees"]  # type: ignore[return-value]


def employees_source() -> str:
    """'db' oder 'demo' – Quelle des letzten get_employees()-Aufrufs."""
    if _CACHE["employees"] is None:
        get_employees()
    return _CACHE["source"]  # type: ignore[return-value]


def reset_employees_cache() -> None:
    _CACHE["employees"] = None
    _CACHE["source"] = "demo"
