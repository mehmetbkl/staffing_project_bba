"""
models(Nico)/forecast_db.py
Persistenz-Schicht für die Besucher-Prognose.

Trennt die Berechnung (futureEXPERT, siehe futureexpert_forecast.py) sauber
von der Speicherung. Damit kann der DB-Write isoliert getestet werden – auch
ohne laufenden futureEXPERT-Job – und die Logik ist an genau einer Stelle.

Schreibt zwei Gold-Tabellen:
  • gold.predictions               – Tagesprognose je Modell/Version (Besucher)
  • gold.staffing_recommendations  – daraus abgeleitete Schicht-Personalempfehlung

Die Schwellenwerte Besucher→Personal sind identisch mit dem Dashboard
(utils/constants.STAFFING_THRESHOLDS) und werden hier gespiegelt, damit das
Modell-Modul ohne Import aus dem Dashboard auskommt.
"""

from __future__ import annotations

import logging
import os
from datetime import date as _date, time as _time

import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


# ── Konfiguration ────────────────────────────────────────────────────────────

# DS-User darf ins Gold-Schema schreiben. Fällt auf die ETL-URL zurück, falls
# DATABASE_URL_DS in der .env (noch) nicht gesetzt ist.
def _database_url() -> str:
    url = os.environ.get("DATABASE_URL_DS") or os.environ.get("DATABASE_URL_ETL")
    if not url:
        raise RuntimeError(
            "Weder DATABASE_URL_DS noch DATABASE_URL_ETL gesetzt – "
            "Prognose kann nicht gespeichert werden."
        )
    return url


# Identisch mit utils/constants.STAFFING_THRESHOLDS im Dashboard.
# (untere Besuchergrenze pro Stunde, empfohlene Mitarbeiterzahl)
STAFFING_THRESHOLDS: list[tuple[int, int]] = [
    (0, 1), (20, 2), (50, 3), (80, 4), (120, 5), (160, 6), (200, 7),
]

# Tagesform (8–21 Uhr): Gewichte zur Verteilung der Tagessumme auf Stunden.
# Spiegelt das Profil aus dem Dashboard, damit DB- und CSV-Pfad gleich aussehen.
_HOURLY_SHAPE = [15, 25, 45, 75, 90, 85, 100, 110, 95, 80, 70, 60, 45, 30]
_OPEN_HOUR = 8

# Schichtdefinition für die Personalempfehlung (Öffnung 8–21 Uhr).
_SHIFTS: list[tuple[str, _time, _time]] = [
    ("Früh",  _time(8, 0),  _time(13, 0)),
    ("Mittag", _time(13, 0), _time(17, 0)),
    ("Spät",  _time(17, 0), _time(21, 0)),
]


def _visitors_to_staff(visitors: float) -> int:
    staff = 1
    for threshold, count in STAFFING_THRESHOLDS:
        if visitors >= threshold:
            staff = count
    return staff


def _demand_level(visitors: float) -> str:
    if visitors >= 120:
        return "hoch"
    if visitors >= 50:
        return "mittel"
    return "niedrig"


# ── gold.predictions ─────────────────────────────────────────────────────────

def write_predictions(
    forecast_df: pd.DataFrame,
    model_name: str,
    model_version: str,
    engine=None,
) -> int:
    """
    Schreibt die Tagesprognose nach gold.predictions.

    Args:
        forecast_df: DataFrame mit Spalten datum, forecast, low, high
                     (genau die Ausgabe von futureexpert_forecast.py).
        model_name:  z. B. "futureEXPERT".
        model_version: z. B. der futureEXPERT-Modellname oder Report-ID.

    Returns:
        Anzahl geschriebener/aktualisierter Zeilen.
    """
    df = _normalize_forecast(forecast_df)
    if df.empty:
        logger.warning("Keine Prognosezeilen zum Speichern.")
        return 0

    engine = engine or create_engine(_database_url())
    rows = 0
    with engine.begin() as conn:
        for r in df.itertuples(index=False):
            conn.execute(text("""
                INSERT INTO gold.predictions
                    (model_name, model_version, timestamp_local,
                     predicted_visitors, confidence_lower, confidence_upper)
                VALUES
                    (:name, :ver, :ts, :pred, :lo, :hi)
                ON CONFLICT (model_name, model_version, timestamp_local)
                DO UPDATE SET
                    predicted_visitors = EXCLUDED.predicted_visitors,
                    confidence_lower   = EXCLUDED.confidence_lower,
                    confidence_upper   = EXCLUDED.confidence_upper,
                    predicted_at       = NOW()
            """), {
                "name": model_name,
                "ver":  model_version,
                "ts":   r.timestamp_local,
                "pred": float(r.forecast),
                "lo":   None if pd.isna(r.low) else float(r.low),
                "hi":   None if pd.isna(r.high) else float(r.high),
            })
            rows += 1
    logger.info("gold.predictions: %s Zeilen geschrieben (%s %s)",
                rows, model_name, model_version)
    print(f"gold.predictions: {rows} Zeilen ({model_name} {model_version})")
    return rows


# ── gold.staffing_recommendations ────────────────────────────────────────────

def write_staffing_recommendations(
    forecast_df: pd.DataFrame,
    model_version: str,
    engine=None,
) -> int:
    """
    Leitet je Prognosetag und Schicht eine Personalempfehlung ab und schreibt
    sie nach gold.staffing_recommendations.

    Die Tages-Besuchersumme wird über das Öffnungszeit-Profil (8–21 Uhr) auf
    Stunden verteilt; pro Schicht wird die Spitzenstunde bewertet (worst case),
    damit die Empfehlung die Belastungsspitze abdeckt statt sie zu mitteln.
    """
    df = _normalize_forecast(forecast_df)
    if df.empty:
        return 0

    engine = engine or create_engine(_database_url())
    rows = 0
    shape_sum = sum(_HOURLY_SHAPE)

    with engine.begin() as conn:
        for r in df.itertuples(index=False):
            day = r.timestamp_local.date() if hasattr(r.timestamp_local, "date") \
                else _date.fromisoformat(str(r.timestamp_local)[:10])
            day_total = float(r.forecast)

            # Stundenverteilung 8..21
            hourly = {
                _OPEN_HOUR + i: day_total * w / shape_sum
                for i, w in enumerate(_HOURLY_SHAPE)
            }

            for shift_name, start, end in _SHIFTS:
                hours = [h for h in hourly if start.hour <= h < end.hour]
                if not hours:
                    continue
                peak = max(hourly[h] for h in hours)        # Spitzenstunde
                total = sum(hourly[h] for h in hours)
                staff = _visitors_to_staff(peak)
                conn.execute(text("""
                    INSERT INTO gold.staffing_recommendations
                        (date_local, shift, shift_start, shift_end,
                         predicted_visitors, recommended_staff, demand_level, model_version)
                    VALUES
                        (:d, :shift, :s, :e, :pv, :staff, :level, :ver)
                    ON CONFLICT (date_local, shift) DO UPDATE SET
                        shift_start        = EXCLUDED.shift_start,
                        shift_end          = EXCLUDED.shift_end,
                        predicted_visitors = EXCLUDED.predicted_visitors,
                        recommended_staff  = EXCLUDED.recommended_staff,
                        demand_level       = EXCLUDED.demand_level,
                        model_version      = EXCLUDED.model_version,
                        created_at         = NOW()
                """), {
                    "d": day, "shift": shift_name, "s": start, "e": end,
                    "pv": int(round(total)), "staff": staff,
                    "level": _demand_level(peak), "ver": model_version,
                })
                rows += 1
    logger.info("gold.staffing_recommendations: %s Zeilen geschrieben", rows)
    print(f"gold.staffing_recommendations: {rows} Zeilen")
    return rows


# ── Hilfsfunktion ────────────────────────────────────────────────────────────

def _normalize_forecast(forecast_df: pd.DataFrame) -> pd.DataFrame:
    """
    Vereinheitlicht die Spalten der futureEXPERT-Ausgabe.

    Erwartet (case-insensitiv): datum/timestamp, forecast, low, high.
    Liefert ein DataFrame mit den Spalten timestamp_local, forecast, low, high.
    """
    if forecast_df is None or len(forecast_df) == 0:
        return pd.DataFrame(columns=["timestamp_local", "forecast", "low", "high"])

    cols = {c.lower(): c for c in forecast_df.columns}
    date_col = cols.get("datum") or cols.get("timestamp_local") or cols.get("time_stamp_utc")
    fc_col = cols.get("forecast") or cols.get("point_forecast_value")
    if date_col is None or fc_col is None:
        raise ValueError(
            f"Forecast-DataFrame braucht Datums- und Forecast-Spalte, "
            f"hat aber: {list(forecast_df.columns)}"
        )

    out = pd.DataFrame()
    out["timestamp_local"] = pd.to_datetime(forecast_df[date_col])
    out["forecast"] = pd.to_numeric(forecast_df[fc_col], errors="coerce")
    out["low"] = pd.to_numeric(forecast_df[cols["low"]], errors="coerce") if "low" in cols else pd.NA
    out["high"] = pd.to_numeric(forecast_df[cols["high"]], errors="coerce") if "high" in cols else pd.NA
    out = out.dropna(subset=["forecast"]).reset_index(drop=True)
    # Negative Prognosen sind fachlich unmöglich → auf 0 kappen (lower_bound).
    out["forecast"] = out["forecast"].clip(lower=0)
    return out
