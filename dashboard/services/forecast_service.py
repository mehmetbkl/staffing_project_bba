"""
services/forecast_service.py
Nachfrageprognose für Dashboard und Prognose-Seite.

Datenquellen in dieser Reihenfolge (graceful Fallback):
  1. gold.predictions          – Vorhersage aus Nicos Modell (DB)
  2. models(Nico)/forecast_besucher.csv – CSV-Ausgabe desselben Modells
  3. Demo-Profil                – festes Tagesprofil, falls nichts da ist

Das Modell liefert eine TAGES-Prognose (Besucher pro Tag, 30 Tage voraus).
Der Intraday-Chart braucht aber ein Stundenprofil. Deshalb wird die echte
Tagessumme auf ein typisches Öffnungszeit-Profil (8–21 Uhr) verteilt – die
angezeigte Tagessumme, die Personalstunden und die Veränderung ggü. Vortag
sind dann echt, die Stundenform ist eine plausible Verteilung.

Interface (DailySummary / ForecastPoint) bleibt für alle Aufrufer identisch.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from services.db import read_sql

logger = logging.getLogger(__name__)

# Typische Tagesform (8–21 Uhr) – Gewichte, auf die eine Tagessumme verteilt wird
_HOURLY_SHAPE = [15, 25, 45, 75, 90, 85, 100, 110, 95, 80, 70, 60, 45, 30]

_CSV_PATH = Path(__file__).resolve().parents[2] / "models(Nico)" / "forecast_besucher.csv"

# Merkt sich die Quelle des letzten Aufrufs für den UI-Hinweis
_SOURCE_STATE = {"forecast": "demo"}  # "db" | "csv" | "demo"


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


# ── Stundenprofil aus einer Tagessumme bauen ─────────────────────────────────

def _build_from_daily_total(
    day_total: int,
    target_day: date,
    change_pct: Optional[float],
    conf_low_total: Optional[int] = None,
    conf_high_total: Optional[int] = None,
) -> DailySummary:
    """Verteilt eine Tages-Besuchersumme auf ein 8–21-Uhr-Stundenprofil."""
    shape_sum = sum(_HOURLY_SHAPE)
    base_dt = datetime.combine(target_day, datetime.min.time()).replace(hour=8)

    points: list[ForecastPoint] = []
    total = 0
    for i, w in enumerate(_HOURLY_SHAPE):
        v = int(round(day_total * w / shape_sum))
        total += v
        ts = base_dt + timedelta(hours=i)
        if conf_low_total is not None and conf_high_total is not None:
            lo = int(round(conf_low_total * w / shape_sum))
            hi = int(round(conf_high_total * w / shape_sum))
        else:
            lo, hi = int(v * 0.85), int(v * 1.15)
        points.append(ForecastPoint(
            timestamp=ts,
            predicted_visitors=v,
            recommended_staff=_visitors_to_staff(v),
            confidence_low=max(0, lo),
            confidence_high=hi,
        ))

    return DailySummary(
        predicted_traffic=total,
        recommended_hours=float(sum(p.recommended_staff for p in points)),
        traffic_change_pct=change_pct,
        points=points,
    )


# ── Quelle 1: gold.predictions ───────────────────────────────────────────────

def _forecast_from_db() -> Optional[DailySummary]:
    """
    Liest die Tagesprognose für heute (oder den nächsten Tag) aus gold.predictions.

    Es können mehrere Modelle Prognosen schreiben (futureEXPERT + Baseline).
    Damit das Dashboard konsistent bleibt, wird genau EIN Modell gewählt –
    bevorzugt futureEXPERT, sonst das zuletzt geschriebene Modell – und davon
    je Tag die jüngste Prognose verwendet.
    """
    df = read_sql("""
        WITH chosen AS (
            SELECT model_name, model_version
            FROM gold.predictions
            WHERE timestamp_local::date >= CURRENT_DATE
            ORDER BY (model_name = 'futureEXPERT') DESC, predicted_at DESC
            LIMIT 1
        ),
        ranked AS (
            SELECT p.timestamp_local::date AS day,
                   p.predicted_visitors,
                   p.confidence_lower,
                   p.confidence_upper,
                   ROW_NUMBER() OVER (
                       PARTITION BY p.timestamp_local::date
                       ORDER BY p.predicted_at DESC
                   ) AS rn
            FROM gold.predictions p
            JOIN chosen c
              ON c.model_name = p.model_name
             AND c.model_version = p.model_version
            WHERE p.timestamp_local::date >= CURRENT_DATE
        )
        SELECT day, predicted_visitors, confidence_lower, confidence_upper
        FROM ranked
        WHERE rn = 1
        ORDER BY day
        LIMIT 2
    """)
    if df is None or df.empty:
        return None

    row = df.iloc[0]
    today_total = int(round(float(row["predicted_visitors"])))
    change = None
    if len(df) > 1:
        nxt = float(df.iloc[1]["predicted_visitors"])
        if today_total:
            change = round((nxt - today_total) / today_total * 100, 1)

    lo = int(round(float(row["confidence_lower"]))) if row["confidence_lower"] is not None else None
    hi = int(round(float(row["confidence_upper"]))) if row["confidence_upper"] is not None else None

    target = row["day"] if hasattr(row["day"], "year") else date.today()
    _SOURCE_STATE["forecast"] = "db"
    logger.info("Prognose: gold.predictions (%d Besucher/Tag)", today_total)
    return _build_from_daily_total(today_total, target, change, lo, hi)


# ── Quelle 2: forecast_besucher.csv ──────────────────────────────────────────

def _forecast_from_csv() -> Optional[DailySummary]:
    """Liest Nicos CSV (Spalten: datum, forecast, low, high)."""
    if not _CSV_PATH.exists():
        return None
    try:
        import pandas as pd
        df = pd.read_csv(_CSV_PATH)
        if df.empty:
            return None
        cols = {c.lower(): c for c in df.columns}
        fc_col = cols.get("forecast")
        if fc_col is None:
            return None
        first = df.iloc[0]
        total = int(round(float(first[fc_col])))
        lo = int(round(float(first[cols["low"]]))) if "low" in cols else None
        hi = int(round(float(first[cols["high"]]))) if "high" in cols else None
        change = None
        if len(df) > 1 and total:
            nxt = float(df.iloc[1][fc_col])
            change = round((nxt - total) / total * 100, 1)
        _SOURCE_STATE["forecast"] = "csv"
        logger.info("Prognose: forecast_besucher.csv (%d Besucher/Tag)", total)
        return _build_from_daily_total(total, date.today(), change, lo, hi)
    except Exception as exc:
        logger.warning("Prognose-CSV konnte nicht gelesen werden: %s", str(exc)[:120])
        return None


# ── Quelle 3: Demo ───────────────────────────────────────────────────────────

def get_placeholder_forecast(
    date: Optional[datetime] = None,
    open_hour: int = 8,
) -> DailySummary:
    """Festes Tagesprofil als Fallback (Demo-Modus)."""
    if date is None:
        date = datetime.now().replace(hour=open_hour, minute=0, second=0, microsecond=0)

    points: list[ForecastPoint] = []
    total = 0
    for i, base in enumerate(_HOURLY_SHAPE):
        ts = date + timedelta(hours=i)
        total += base
        points.append(ForecastPoint(
            timestamp=ts,
            predicted_visitors=base,
            recommended_staff=_visitors_to_staff(base),
            confidence_low=max(0, int(base * 0.85)),
            confidence_high=int(base * 1.15),
        ))
    return DailySummary(
        predicted_traffic=total,
        recommended_hours=float(sum(p.recommended_staff for p in points)),
        traffic_change_pct=-12.0,
        points=points,
    )


# ── Öffentliche API ──────────────────────────────────────────────────────────

def get_forecast() -> DailySummary:
    """Beste verfügbare Prognose: DB → CSV → Demo."""
    result = _forecast_from_db()
    if result is not None:
        return result
    result = _forecast_from_csv()
    if result is not None:
        return result
    _SOURCE_STATE["forecast"] = "demo"
    return get_placeholder_forecast()


def forecast_source() -> str:
    """Quelle des letzten get_forecast()-Aufrufs: 'db', 'csv' oder 'demo'."""
    return _SOURCE_STATE["forecast"]
