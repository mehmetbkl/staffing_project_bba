from sqlalchemy import text
from etl.db import engine

def load_library(df):
    with engine.begin() as conn:
        for row in df.itertuples(index=False):
            conn.execute(text("""
                INSERT INTO raw.library_visitors (timestamp_local, count_enter, count_exit)
                VALUES (:ts, :enter, :exit)
                ON CONFLICT (timestamp_local) DO NOTHING
            """), {"ts": row.timestamp, "enter": row.count_enter, "exit": row.count_exit})
    print(f"Loaded: {len(df)} rows")

def load_weather(df):
    with engine.begin() as conn:
        for row in df.itertuples(index=False):
            conn.execute(text("""
                INSERT INTO raw.weather
                    (timestamp_local, temperature_c, precipitation_mm, weather_code, wind_speed_kmh, cloud_cover_pct)
                VALUES
                    (:ts, :temp, :precip, :code, :wind, :cloud)
                ON CONFLICT (timestamp_local) DO NOTHING
            """), {
                "ts":     row.timestamp_local,
                "temp":   row.temperature_c,
                "precip": row.precipitation_mm,
                "code":   row.weather_code,
                "wind":   row.wind_speed_kmh,
                "cloud":  row.cloud_cover_pct,
            })
    print(f"Loaded: {len(df)} rows")

def load_holidays(df):
    with engine.begin() as conn:
        for row in df.itertuples(index=False):
            conn.execute(text("""
                INSERT INTO processed.holidays
                    (date_local, is_public_holiday, is_school_holiday, holiday_name)
                VALUES
                    (:date, :public, :school, :name)
                ON CONFLICT (date_local) DO NOTHING
            """), {
                "date":   row.date_local,
                "public": row.is_public_holiday,
                "school": row.is_school_holiday,
                "name":   row.holiday_name,
            })
    print(f"Loaded: {len(df)} rows")