"""
etl/loaders/postgres.py
Lädt die Roh-/Processed-Daten in die NeonDB.

Batch-Inserts: Statt je Zeile einen eigenen Round-Trip zur DB (bei >10.000
Wetterzeilen führte das zum 15-Minuten-Timeout im GitHub-Cron) werden die
Zeilen in Blöcken via executemany geschrieben – eine Parameterliste je Block.
Logik unverändert: weiterhin idempotent über ON CONFLICT ... DO NOTHING.
"""

from sqlalchemy import text
from etl.db import engine

# Zeilen pro Insert-Block. Groß genug für wenige Round-Trips, klein genug,
# dass die Parameteranzahl je Statement im Rahmen bleibt.
CHUNK_SIZE = 1000


def _clean(value):
    """pandas/numpy-Skalare in native Python-Typen wandeln (psycopg2-freundlich).

    NaN/NaT wird zu None (→ SQL NULL). Alles andere über .item() entpackt,
    falls es ein numpy-Typ ist.
    """
    try:
        import pandas as pd
        if value is None or (not isinstance(value, str) and pd.isna(value)):
            return None
    except Exception:
        if value is None:
            return None
    item = getattr(value, "item", None)
    return item() if callable(item) else value


def _executemany(conn, sql: str, params: list[dict]) -> None:
    """Führt einen INSERT für eine Parameterliste blockweise aus."""
    stmt = text(sql)
    for i in range(0, len(params), CHUNK_SIZE):
        conn.execute(stmt, params[i:i + CHUNK_SIZE])


def load_library(df):
    sql = """
        INSERT INTO raw.library_visitors (timestamp_local, count_enter, count_exit)
        VALUES (:ts, :enter, :exit)
        ON CONFLICT (timestamp_local) DO NOTHING
    """
    params = [
        {
            "ts":    _clean(row.timestamp),
            "enter": _clean(row.count_enter),
            "exit":  _clean(row.count_exit),
        }
        for row in df.itertuples(index=False)
    ]
    with engine.begin() as conn:
        _executemany(conn, sql, params)
    print(f"Loaded: {len(df)} rows")


def load_weather(df):
    sql = """
        INSERT INTO raw.weather
            (timestamp_local, temperature_c, precipitation_mm, weather_code, wind_speed_kmh, cloud_cover_pct)
        VALUES
            (:ts, :temp, :precip, :code, :wind, :cloud)
        ON CONFLICT (timestamp_local) DO NOTHING
    """
    params = [
        {
            "ts":     _clean(row.timestamp_local),
            "temp":   _clean(row.temperature_c),
            "precip": _clean(row.precipitation_mm),
            "code":   _clean(row.weather_code),
            "wind":   _clean(row.wind_speed_kmh),
            "cloud":  _clean(row.cloud_cover_pct),
        }
        for row in df.itertuples(index=False)
    ]
    with engine.begin() as conn:
        _executemany(conn, sql, params)
    print(f"Loaded: {len(df)} rows")


def load_holidays(df):
    sql = """
        INSERT INTO processed.holidays
            (date_local, is_public_holiday, is_school_holiday, holiday_name)
        VALUES
            (:date, :public, :school, :name)
        ON CONFLICT (date_local) DO NOTHING
    """
    params = [
        {
            "date":   _clean(row.date_local),
            "public": _clean(row.is_public_holiday),
            "school": _clean(row.is_school_holiday),
            "name":   _clean(row.holiday_name),
        }
        for row in df.itertuples(index=False)
    ]
    with engine.begin() as conn:
        _executemany(conn, sql, params)
    print(f"Loaded: {len(df)} rows")
