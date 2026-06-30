"""
services/history_service.py
Historiendaten für den Historie-/Trends-Tab.

Liest – wenn verfügbar – echte Daten aus der NeonDB:
    raw.library_visitors  (count_enter je Stunde)
    raw.weather           (Temperatur, Niederschlag je Stunde)

Ist die DB nicht erreichbar oder leer, wird automatisch ein stabiles
Demo-Profil verwendet (graceful Fallback). is_live() sagt, was gerade gilt.
"""

from __future__ import annotations
import logging
import math
from dataclasses import dataclass
from datetime import date, timedelta

from services.db import read_sql

logger = logging.getLogger(__name__)

_WEEKDAYS_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

# Merkt sich nach dem ersten Laden, ob echte Daten kamen (für UI-Hinweis)
_LIVE_STATE = {"history": False}


@dataclass
class DayStat:
    day_label: str
    iso_date: str
    visitors: int
    avg_temp_c: float
    rain_mm: float


# ── DEMO-DATEN (Fallback) ────────────────────────────────────────────────────

def _seeded(n: int) -> float:
    """Deterministischer Pseudo-Zufall, damit die Demo stabil bleibt."""
    return (math.sin(n * 12.9898) * 43758.5453) % 1.0


def _demo_last_30_days() -> list[DayStat]:
    today = date.today()
    stats: list[DayStat] = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        wd = d.weekday()
        base = 720 if wd < 5 else 430
        temp = 14 + 8 * _seeded(i) + (3 if wd < 5 else 0)
        rain = round(max(0.0, (_seeded(i * 3) - 0.6) * 12), 1)
        weekday_noise = (_seeded(i * 7) - 0.5) * 180
        rain_penalty = rain * 9
        visitors = int(max(120, base + weekday_noise - rain_penalty))
        stats.append(DayStat(
            day_label=_WEEKDAYS_DE[wd],
            iso_date=d.isoformat(),
            visitors=visitors,
            avg_temp_c=round(temp, 1),
            rain_mm=rain,
        ))
    return stats


def _demo_hourly_profile() -> list[dict]:
    profile = [120, 210, 360, 540, 690, 760, 800, 880,
               820, 700, 600, 500, 360, 220, 110]
    return [{"hour": f"{8 + i:02d}:00", "visitors": v} for i, v in enumerate(profile)]


# ── DB-ABFRAGEN ──────────────────────────────────────────────────────────────

def _db_last_30_days() -> list[DayStat] | None:
    """
    Aggregiert die letzten 30 Tage mit Daten aus raw.library_visitors
    (Summe count_enter je Tag) und raw.weather (Ø Temp, Σ Regen je Tag).
    Gibt None zurück, wenn keine Daten vorliegen.
    """
    df = read_sql("""
        WITH v AS (
            SELECT (timestamp_local AT TIME ZONE 'Europe/Berlin')::date AS d,
                   SUM(count_enter) AS visitors
            FROM raw.library_visitors
            GROUP BY 1
        ),
        w AS (
            SELECT (timestamp_local AT TIME ZONE 'Europe/Berlin')::date AS d,
                   AVG(temperature_c)   AS avg_temp,
                   SUM(precipitation_mm) AS rain
            FROM raw.weather
            GROUP BY 1
        )
        SELECT v.d AS day, v.visitors,
               w.avg_temp, w.rain
        FROM v LEFT JOIN w ON v.d = w.d
        WHERE v.visitors IS NOT NULL
        ORDER BY v.d DESC
        LIMIT 30
    """)
    if df is None or df.empty:
        return None

    df = df.sort_values("day")
    stats: list[DayStat] = []
    for row in df.itertuples(index=False):
        d = row.day
        iso = d.isoformat() if hasattr(d, "isoformat") else str(d)
        wd = d.weekday() if hasattr(d, "weekday") else date.fromisoformat(iso).weekday()
        temp = float(row.avg_temp) if row.avg_temp is not None else 0.0
        rain = float(row.rain) if row.rain is not None else 0.0
        stats.append(DayStat(
            day_label=_WEEKDAYS_DE[wd],
            iso_date=iso,
            visitors=int(row.visitors),
            avg_temp_c=round(temp, 1),
            rain_mm=round(rain, 1),
        ))
    return stats or None


def _db_hourly_profile() -> list[dict] | None:
    """Ø count_enter je Öffnungsstunde (8–22 Uhr) über alle Tage."""
    df = read_sql("""
        SELECT EXTRACT(HOUR FROM timestamp_local AT TIME ZONE 'Europe/Berlin')::int AS hour,
               AVG(count_enter) AS avg_enter
        FROM raw.library_visitors
        GROUP BY 1
        ORDER BY 1
    """)
    if df is None or df.empty:
        return None
    by_hour = {int(r.hour): float(r.avg_enter or 0) for r in df.itertuples(index=False)}
    out = []
    for h in range(8, 23):
        if h in by_hour:
            out.append({"hour": f"{h:02d}:00", "visitors": int(round(by_hour[h]))})
    return out or None


# ── ÖFFENTLICHE API (DB → sonst Demo) ────────────────────────────────────────

def get_last_30_days() -> list[DayStat]:
    db = _db_last_30_days()
    if db:
        _LIVE_STATE["history"] = True
        return db
    _LIVE_STATE["history"] = False
    return _demo_last_30_days()


def get_hourly_profile() -> list[dict]:
    db = _db_hourly_profile()
    if db:
        return db
    return _demo_hourly_profile()


def is_live() -> bool:
    """True, wenn der letzte get_last_30_days()-Aufruf echte DB-Daten lieferte."""
    return _LIVE_STATE["history"]


def get_weekday_profile() -> list[dict]:
    days = get_last_30_days()
    buckets: dict[str, list[int]] = {wd: [] for wd in _WEEKDAYS_DE}
    for d in days:
        buckets[d.day_label].append(d.visitors)
    return [
        {"weekday": wd, "avg_visitors": int(sum(v) / len(v)) if v else 0}
        for wd, v in buckets.items()
    ]


def get_weather_correlation() -> list[dict]:
    return [
        {"temp": d.avg_temp_c, "visitors": d.visitors, "rain": d.rain_mm}
        for d in get_last_30_days()
    ]


def get_history_summary() -> dict:
    days = get_last_30_days()
    visitors = [d.visitors for d in days]
    total = sum(visitors)
    avg = int(total / len(visitors)) if visitors else 0
    busiest = max(days, key=lambda d: d.visitors)
    quietest = min(days, key=lambda d: d.visitors)
    return {
        "avg_per_day": avg,
        "total_30d": total,
        "busiest_value": busiest.visitors,
        "busiest_date": busiest.iso_date,
        "quietest_value": quietest.visitors,
        "quietest_date": quietest.iso_date,
        "days_count": len(days),
    }
