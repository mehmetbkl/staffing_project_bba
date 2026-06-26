"""
services/forecast_service.py
Platzhalter-Prognose bis Nicos ANN-Modell verfügbar ist.
Interface bleibt bei Modell-Integration identisch.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ForecastPoint:
    timestamp: datetime
    predicted_visitors: int
    recommended_staff: int
    confidence_low: Optional[int] = None
    confidence_high: Optional[int] = None


@dataclass
class DailySummary:
    predicted_traffic: int
    recommended_hours: float
    traffic_change_pct: Optional[float]
    points: list[ForecastPoint] = field(default_factory=list)


def _visitors_to_staff(visitors: int) -> int:
    from utils.constants import STAFFING_THRESHOLDS
    staff = 1
    for threshold, count in STAFFING_THRESHOLDS:
        if visitors >= threshold:
            staff = count
    return staff


def get_placeholder_forecast(
    date: Optional[datetime] = None,
    open_hour: int = 8,
) -> DailySummary:
    """
    Statisches Tagesprofil für Demo-Zwecke.

    INTEGRATION: Diese Funktion durch Nicos Modell-Aufruf ersetzen.
    DailySummary + ForecastPoint Interface bleibt identisch.
    """
    if date is None:
        date = datetime.now().replace(
            hour=open_hour, minute=0, second=0, microsecond=0
        )

    _profile = [15, 25, 45, 75, 90, 85, 100, 110, 95, 80, 70, 60, 45, 30]

    points: list[ForecastPoint] = []
    total = 0
    for i, base in enumerate(_profile):
        ts = date + timedelta(hours=i)
        staff = _visitors_to_staff(base)
        total += base
        points.append(ForecastPoint(
            timestamp=ts,
            predicted_visitors=base,
            recommended_staff=staff,
            confidence_low=max(0, int(base * 0.85)),
            confidence_high=int(base * 1.15),
        ))

    return DailySummary(
        predicted_traffic=total,
        recommended_hours=float(sum(p.recommended_staff for p in points)),
        traffic_change_pct=-12.0,
        points=points,
    )