# dashboard/services/shift_service.py
#
# Liest den Schichtplan aus data/employees.py und berechnet
# automatisch den Status jedes Mitarbeiters anhand der aktuellen Uhrzeit.

from __future__ import annotations
from datetime import datetime
from data.employees import EMPLOYEES

# Pause wird angenommen wenn die Schicht > 4h ist und man in der Mitte ist
BREAK_BUFFER_MINUTES = 30


def _parse_time(t: str) -> datetime:
    """Wandelt 'HH:MM' in ein datetime-Objekt (heute) um."""
    h, m = map(int, t.split(":"))
    return datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)


def _get_status(start_str: str, end_str: str, now: datetime) -> str:
    """
    Bestimmt den Status eines Mitarbeiters anhand der aktuellen Zeit.

    Returns:
        "active"  – gerade im Dienst
        "break"   – im Dienst, aber Pause (grobe Schätzung Mitte der Schicht)
        "coming"  – kommt noch
        "done"    – Schicht beendet
    """
    start = _parse_time(start_str)
    end   = _parse_time(end_str)

    if now < start:
        return "coming"
    if now > end:
        return "done"

    # Pausenfenster: 30 min rund um die Schichtmitte
    mid        = start + (end - start) / 2
    break_start = mid.replace(minute=mid.minute - BREAK_BUFFER_MINUTES
                              if mid.minute >= BREAK_BUFFER_MINUTES
                              else mid.minute)
    break_end   = mid.replace(minute=min(mid.minute + BREAK_BUFFER_MINUTES, 59))

    if break_start <= now <= break_end:
        return "break"

    return "active"


def get_todays_shifts() -> list[dict]:
    """
    Gibt alle Mitarbeiter zurück, die heute eingeplant sind.

    Returns Liste von:
        {
          "id":     "AK",
          "name":   "Anna K.",
          "role":   "Kassierer",
          "start":  "08:00",
          "end":    "14:00",
          "status": "active" | "break" | "coming" | "done"
        }
    """
    now     = datetime.now()
    weekday = now.strftime("%a")  # "Mon", "Tue", ...

    result = []
    for emp in EMPLOYEES:
        shift = emp["shifts"].get(weekday)
        if shift is None:
            continue  # heute kein Dienst

        start, end = shift
        result.append({
            "id":     emp["id"],
            "name":   emp["name"],
            "role":   emp["role"],
            "start":  start,
            "end":    end,
            "status": _get_status(start, end, now),
        })

    # Sortierung: aktive zuerst, dann Pause, dann kommend, dann fertig
    order = {"active": 0, "break": 1, "coming": 2, "done": 3}
    result.sort(key=lambda x: (order[x["status"]], x["start"]))
    return result


def get_shift_summary() -> dict:
    """
    Kurzübersicht für die KPI-Karte oder den Coverage-Balken.

    Returns:
        {
          "total_today":  3,     – Mitarbeiter im Dienst heute
          "active_now":   2,     – gerade aktiv oder Pause
          "coming":       1,     – starten noch heute
          "coverage_pct": 67     – aktive / gesamt * 100
        }
    """
    shifts      = get_todays_shifts()
    total       = len(shifts)
    active_now  = sum(1 for s in shifts if s["status"] in ("active", "break"))
    coming      = sum(1 for s in shifts if s["status"] == "coming")
    coverage    = round(active_now / total * 100) if total > 0 else 0

    return {
        "total_today":  total,
        "active_now":   active_now,
        "coming":       coming,
        "coverage_pct": coverage,
    }