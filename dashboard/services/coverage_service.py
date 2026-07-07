"""
services/coverage_service.py
Bedarf-vs-Besetzung: Vergleicht den stündlichen Personal-BEDARF (aus der
Prognose, ForecastPoint.recommended_staff) mit der tatsächlich für heute
EINGEPLANTEN Besetzung (Schichtplan aus shift_service / employees).

Ergebnis je Stunde:
    required   – empfohlene Mitarbeiter laut Prognose
    scheduled  – wie viele Mitarbeiter in dieser Stunde im Dienst sind
    gap        – scheduled - required  (negativ = Unterdeckung)

Abwesende Mitarbeiter (Urlaub/krank, siehe data/absences.py) zählen NICHT
zur eingeplanten Besetzung – so wirkt sich Abwesenheit direkt auf die Deckung aus.
"""

from __future__ import annotations
from datetime import datetime

from services.forecast_service import get_forecast
from data.employees import get_employees

try:
    # Abwesenheiten sind optional – ohne die Datei läuft die Deckung trotzdem.
    from data.absences import is_absent_today
except Exception:  # pragma: no cover
    def is_absent_today(emp_id: str) -> bool:
        return False


def _hour_of(hhmm: str) -> int:
    return int(hhmm.split(":")[0])


def _scheduled_at_hour(hour: int, weekday: str) -> int:
    """Zählt heute eingeplante, NICHT abwesende Mitarbeiter, die in [hour, hour+1) arbeiten."""
    count = 0
    for emp in get_employees():
        if is_absent_today(emp["id"]):
            continue
        shift = emp["shifts"].get(weekday)
        if not shift:
            continue
        start_h = _hour_of(shift[0])
        end_h = _hour_of(shift[1])
        if start_h <= hour < end_h:
            count += 1
    return count


def get_coverage_today() -> list[dict]:
    """
    Baut die stündliche Deckungstabelle für heute.

    Returns Liste von:
        {"hour_label": "08:00", "hour": 8,
         "required": 3, "scheduled": 2, "gap": -1,
         "status": "under" | "over" | "ok"}
    """
    forecast = get_forecast()
    weekday = datetime.now().strftime("%a")  # "Mon", ...

    rows: list[dict] = []
    for p in forecast.points:
        hour = p.timestamp.hour
        required = p.recommended_staff
        scheduled = _scheduled_at_hour(hour, weekday)
        gap = scheduled - required
        if gap < 0:
            status = "under"
        elif gap > 0:
            status = "over"
        else:
            status = "ok"
        rows.append({
            "hour_label": p.timestamp.strftime("%H:%M"),
            "hour": hour,
            "required": required,
            "scheduled": scheduled,
            "gap": gap,
            "status": status,
        })
    return rows


def get_coverage_summary() -> dict:
    """
    Kennzahlen für die KPI-Leiste der Deckungs-Seite.

    Returns:
        {
          "under_hours":   Anzahl Stunden mit Unterdeckung,
          "over_hours":    Anzahl Stunden mit Überdeckung,
          "ok_hours":      Anzahl exakt gedeckter Stunden,
          "peak_gap_hour": Stunde mit größter Unterdeckung ("–" wenn keine),
          "peak_gap":      größte Unterdeckung (positiv, Anzahl fehlender MA),
          "coverage_pct":  Anteil ausreichend gedeckter Stunden (ok+over) in %,
          "total_required":  Summe benötigter Personalstunden,
          "total_scheduled": Summe eingeplanter Personalstunden,
        }
    """
    rows = get_coverage_today()
    if not rows:
        return {
            "under_hours": 0, "over_hours": 0, "ok_hours": 0,
            "peak_gap_hour": "–", "peak_gap": 0, "coverage_pct": 0,
            "total_required": 0, "total_scheduled": 0,
        }

    under = [r for r in rows if r["status"] == "under"]
    over = [r for r in rows if r["status"] == "over"]
    ok = [r for r in rows if r["status"] == "ok"]
    covered = len(ok) + len(over)

    if under:
        worst = min(under, key=lambda r: r["gap"])  # gap am negativsten
        peak_gap_hour = worst["hour_label"]
        peak_gap = -worst["gap"]
    else:
        peak_gap_hour = "–"
        peak_gap = 0

    return {
        "under_hours": len(under),
        "over_hours": len(over),
        "ok_hours": len(ok),
        "peak_gap_hour": peak_gap_hour,
        "peak_gap": peak_gap,
        "coverage_pct": round(covered / len(rows) * 100),
        "total_required": sum(r["required"] for r in rows),
        "total_scheduled": sum(r["scheduled"] for r in rows),
    }
