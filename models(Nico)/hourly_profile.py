"""
models(Nico)/hourly_profile.py
Stundenprofil & Disaggregation: verteilt die Tagesprognose auf Stunden.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_FALLBACK_SHAPE = [15, 25, 45, 75, 90, 85, 100, 110, 95, 80, 70, 60, 45, 30]
_FALLBACK_OPEN_HOUR = 8

HOURS = list(range(24))
WEEKDAYS = list(range(1, 8))  # 1=Mo .. 7=So (ISO)


def fallback_profile() -> pd.DataFrame:
    """Festes 8-21-Uhr-Profil als DataFrame (Index Wochentag 1-7, Spalten 0-23)."""
    shares = np.zeros(24)
    total = float(sum(_FALLBACK_SHAPE))
    for i, w in enumerate(_FALLBACK_SHAPE):
        shares[_FALLBACK_OPEN_HOUR + i] = w / total
    return pd.DataFrame([shares] * 7, index=WEEKDAYS, columns=HOURS)


def build_profile(hourly_visitors: pd.DataFrame) -> pd.DataFrame:
    if hourly_visitors is None or hourly_visitors.empty:
        logger.warning("Keine Stundendaten - nutze Fallback-Profil.")
        return fallback_profile()

    df = hourly_visitors.copy()
    ts = pd.to_datetime(df["timestamp_local"], utc=True).dt.tz_convert("Europe/Berlin")
    df["day"] = ts.dt.date
    df["weekday"] = ts.dt.dayofweek + 1
    df["hour"] = ts.dt.hour

    mat = (
        df.pivot_table(index=["day", "weekday"], columns="hour",
                       values="count_enter", aggfunc="sum", fill_value=0)
        .reindex(columns=HOURS, fill_value=0)
    )
    day_totals = mat.sum(axis=1)
    mat = mat[day_totals > 0]
    if mat.empty:
        logger.warning("Alle Tage leer - nutze Fallback-Profil.")
        return fallback_profile()

    shares = mat.div(mat.sum(axis=1), axis=0)
    profile = shares.groupby(level="weekday").median()
    profile = profile.reindex(WEEKDAYS)

    overall = shares.median(axis=0)
    for wd in WEEKDAYS:
        if profile.loc[wd].isna().all() or profile.loc[wd].sum() <= 0:
            profile.loc[wd] = overall

    profile = profile.fillna(0.0)
    profile = profile.div(profile.sum(axis=1), axis=0).fillna(0.0)
    return profile


def load_profile(engine) -> pd.DataFrame:
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            df = pd.read_sql(text("""
                SELECT timestamp_local, count_enter
                FROM raw.library_visitors
            """), conn)
        profile = build_profile(df)
        logger.info("Stundenprofil aus %s Zeilen Historie gelernt.", len(df))
        return profile
    except Exception as exc:
        logger.warning("Stundenprofil nicht ladbar (%s) - Fallback-Profil.", exc)
        return fallback_profile()


def disaggregate(daily_forecast: pd.DataFrame,
                 profile: pd.DataFrame) -> pd.DataFrame:
    has_horizon = "horizont" in daily_forecast.columns
    rows: list[dict] = []
    for r in daily_forecast.itertuples(index=False):
        day = pd.to_datetime(r.datum)
        weekday = int(day.dayofweek) + 1
        shares = profile.loc[weekday] if weekday in profile.index \
            else fallback_profile().loc[weekday]
        for hour, share in shares.items():
            share = float(share)
            if share <= 0:
                continue
            row = {
                "timestamp_local": day.replace(hour=int(hour)),
                "forecast": round(float(r.forecast) * share, 1),
                "low": round(float(r.low) * share, 1) if pd.notna(r.low) else None,
                "high": round(float(r.high) * share, 1) if pd.notna(r.high) else None,
            }
            if has_horizon:
                row["horizont"] = r.horizont
            rows.append(row)
    out = pd.DataFrame(rows).sort_values("timestamp_local").reset_index(drop=True)
    return out
