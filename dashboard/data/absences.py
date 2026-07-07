"""
data/absences.py
Abwesenheiten (Urlaub / krank) je Mitarbeiter.

Demo-Datensatz mit Zeiträumen; später leicht durch eine DB-Tabelle
(z. B. staff.absences) ersetzbar. Ein abwesender Mitarbeiter zählt nicht zur
eingeplanten Besetzung (siehe coverage_service) und wird im Schichtplan sowie
in der Schichtübersicht entsprechend markiert.

Zeitraum inklusive: start <= heute <= end.
"""

from __future__ import annotations
from datetime import date, datetime

# emp_id -> Liste von (typ, start_iso, end_iso)
# typ: "vacation" (Urlaub) | "sick" (krank)
ABSENCES: dict[str, list[tuple[str, str, str]]] = {
    # Beispiele relativ offen gehalten, damit im Demo-Modus etwas sichtbar ist.
    "SB": [("vacation", "2000-01-01", "2999-12-31")],  # dauerhaft im Demo abwesend
    "MR": [("sick",     "2000-01-01", "2999-12-31")],
}

_TYPE_LABEL = {
    "vacation": "Urlaub",
    "sick": "Krank",
}


def _parse(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()


def get_absence_today(emp_id: str) -> dict | None:
    """
    Gibt die heute gültige Abwesenheit eines Mitarbeiters zurück oder None.

    Returns z. B. {"type": "vacation", "label": "Urlaub"} oder None.
    """
    today = date.today()
    for typ, start, end in ABSENCES.get(emp_id, []):
        try:
            if _parse(start) <= today <= _parse(end):
                return {"type": typ, "label": _TYPE_LABEL.get(typ, "Abwesend")}
        except ValueError:
            continue
    return None


def is_absent_today(emp_id: str) -> bool:
    """True, wenn der Mitarbeiter heute abwesend (Urlaub/krank) ist."""
    return get_absence_today(emp_id) is not None


def get_absent_ids_today() -> set[str]:
    """Menge aller heute abwesenden Mitarbeiter-IDs."""
    return {emp_id for emp_id in ABSENCES if is_absent_today(emp_id)}
