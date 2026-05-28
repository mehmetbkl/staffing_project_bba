# models(Nico)/futureexpert_forecast.py

import os
import time
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from futureexpert import ExpertClient
from futureexpert.checkin import (
    DataDefinition, DateColumn, ValueColumn, TsCreationConfig
)
from futureexpert.forecast import ReportConfig, ForecastingConfig, PreprocessingConfig

# ── KONFIGURATION ─────────────────────────────────────────────────────────────
load_dotenv()
HORIZON = 30  # 30 Tage voraus forecasten

# ── 1. DATEN AUS NEON DB LADEN ────────────────────────────────────────────────
print("Verbinde mit Neon DB...")
engine = create_engine(os.environ["DATABASE_URL_DS"])

with engine.connect() as conn:
    visitors_raw = pd.read_sql(text("""
        SELECT timestamp_local, count_enter
        FROM raw.library_visitors
        ORDER BY timestamp_local
    """), conn)

    weather_raw = pd.read_sql(text("""
        SELECT timestamp_local, temperature_c, precipitation_mm
        FROM raw.weather
        ORDER BY timestamp_local
    """), conn)

print(f"  Besucher: {len(visitors_raw)} Zeilen")
print(f"  Wetter:   {len(weather_raw)} Zeilen")


# ── 2. STÜNDLICH → TÄGLICH AGGREGIEREN ───────────────────────────────────────
visitors_raw["timestamp_local"] = pd.to_datetime(visitors_raw["timestamp_local"], utc=True)
weather_raw["timestamp_local"]  = pd.to_datetime(weather_raw["timestamp_local"],  utc=True)

visitors_daily = (
    visitors_raw
    .groupby(visitors_raw["timestamp_local"].dt.date)["count_enter"]
    .sum()
    .reset_index()
    .rename(columns={"timestamp_local": "datum", "count_enter": "besucher"})
)
visitors_daily["datum"] = pd.to_datetime(visitors_daily["datum"])

weather_daily = (
    weather_raw
    .groupby(weather_raw["timestamp_local"].dt.date)
    .agg(
        temperature_c=("temperature_c", "mean"),
        precipitation_mm=("precipitation_mm", "sum")
    )
    .reset_index()
    .rename(columns={"timestamp_local": "datum"})
)
weather_daily["datum"] = pd.to_datetime(weather_daily["datum"])

print(f"\nNach Aggregation:")
print(f"  Besucher (täglich): {len(visitors_daily)} Tage")
print(visitors_daily.head(3).to_string(index=False))


# ── 3. FUTUREEXPERT LOGIN ─────────────────────────────────────────────────────
print("\nLogge ein bei futureEXPERT...")
client = ExpertClient.from_user_password()


# ── 4. CHECK-IN BESUCHER-ZEITREIHE ───────────────────────────────────────────
print("\nCHECK-IN Besucherdaten...")

visitors_csv = "models(Nico)/visitors_daily.csv"
visitors_daily.to_csv(visitors_csv, index=False, date_format="%Y-%m-%d")

version_visitors = client.check_in_time_series(
    raw_data_source=visitors_csv,
    data_definition=DataDefinition(
        date_column=DateColumn(name="datum", format="%Y-%m-%d"),
        value_columns=[ValueColumn(name="besucher")],
    ),
    config_ts_creation=TsCreationConfig(
        time_granularity="daily",
        value_columns_to_save=["besucher"]
    )
)
print(f"  Version ID (Besucher): {version_visitors}")


# ── 5. CHECK-IN WETTER ALS KOVARIATE ─────────────────────────────────────────
print("\nCHECK-IN Wetterdaten als Kovariate...")

weather_csv = "models(Nico)/weather_daily.csv"
weather_daily.to_csv(weather_csv, index=False, date_format="%Y-%m-%d")

version_weather = client.check_in_time_series(
    raw_data_source=weather_csv,
    data_definition=DataDefinition(
        date_column=DateColumn(name="datum", format="%Y-%m-%d"),
        value_columns=[
            ValueColumn(name="temperature_c"),
            ValueColumn(name="precipitation_mm"),
        ],
    ),
    config_ts_creation=TsCreationConfig(
        time_granularity="daily",
        value_columns_to_save=["temperature_c", "precipitation_mm"]
    )
)
print(f"  Version ID (Wetter): {version_weather}")


# ── 6. FORECAST STARTEN ───────────────────────────────────────────────────────
print("\nStarte FORECAST...")

fc_config = ReportConfig(
    title="Staffing-Forecast Bibliothek Hubland",
    forecasting=ForecastingConfig(
        fc_horizon=HORIZON,
        lower_bound=0.0,
        round_forecast_to_integer=True,
    ),
    preprocessing=PreprocessingConfig(
        detect_outliers=True,
        replace_outliers=True,
        detect_changepoints=True,
    )
)

report_id = client.start_forecast(version=version_visitors, config=fc_config)
print(f"  Report ID: {report_id.report_id} – Forecast läuft...")


# ── 7. AUF ERGEBNIS WARTEN ────────────────────────────────────────────────────
print("\nWarte auf Ergebnis", end="", flush=True)
while True:
    status = client.get_report_status(id=report_id)
    if status.is_finished:
        print(" ✓")
        break
    print(".", end="", flush=True)
    time.sleep(10)


# ── 8. ERGEBNISSE SPEICHERN ───────────────────────────────────────────────────
print("\nLade Ergebnisse...")
results = client.get_fc_results(
    id=report_id,
    include_k_best_models=1,
    include_backtesting=True
)

output_dir = os.path.dirname(os.path.abspath(__file__))

for fc in results.forecast_results:
    best = fc.best_model
    if best is None:
        print("Kein Modell gefunden.")
        continue

    fc_df = pd.DataFrame([{
        "datum":    v.time_stamp_utc,
        "forecast": v.point_forecast_value,
        "low":      v.lower_limit_value,
        "high":     v.upper_limit_value
    } for v in best.forecasts])

    out_path = os.path.join(output_dir, "forecast_besucher.csv")
    fc_df.to_csv(out_path, index=False)

    print(f"\nModell: {best.model_name}")
    print(fc_df.to_string(index=False))
    print(f"\nGespeichert: {out_path}")

print("\nFertig!")