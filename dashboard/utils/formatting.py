"""
utils/formatting.py
Hilfsfunktionen für Formatierung.
"""

from __future__ import annotations
from datetime import datetime

_WEEKDAYS_DE = [
    "Montag", "Dienstag", "Mittwoch", "Donnerstag",
    "Freitag", "Samstag", "Sonntag",
]
_MONTHS_DE = [
    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


def format_date_de(dt: datetime | None = None) -> str:
    if dt is None:
        dt = datetime.now()
    return f"{_WEEKDAYS_DE[dt.weekday()]}, {dt.day}. {_MONTHS_DE[dt.month]} {dt.year}"


def format_temperature(value: float | None, unit: str = "°C") -> str:
    return f"{value:.1f} {unit}" if value is not None else "–"


def format_wind_speed(value: float | None) -> str:
    return f"{value:.0f} km/h" if value is not None else "–"


def format_precipitation(value: float | None) -> str:
    return f"{value:.1f} mm" if value is not None else "–"


def format_cloud_cover(value: float | None) -> str:
    return f"{value:.0f} %" if value is not None else "–"


def format_visitors(value: int | float | None) -> str:
    return f"{int(value):,}".replace(",", ".") if value is not None else "–"


def format_hours(value: float | None) -> str:
    return f"{value:.1f} h" if value is not None else "–"