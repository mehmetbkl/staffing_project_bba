# models(Nico)/futureexpert_forecast.py
#
# Besucher-Forecast über futureEXPERT (prognostica) mit zwei Horizonten:
#
#   * DETAIL (10 Tage):  nutzt den eigenen Wetter-Forecast (weather_forecast.py)
#                        als Zukunfts-Kovariate. Der futureEXPERT-Matcher prüft
#                        vorab, ob Temperatur/Niederschlag die Prognose messbar
#                        verbessern (Kovariaten-Ranking).
#   * GROB   (30 Tage):  univariat, ohne Wetter. Bewusst, denn jenseits von
#                        ~14 Tagen hat eine Wettervorhersage keine Vorhersage-
#                        kraft mehr – eine Schein-Kovariate würde das Modell
#                        nur verschlechtern (Garbage in, garbage out).
#
# Ergebnis: Tag 1–10 aus dem Detail-Forecast, Tag 11–30 aus dem Grob-Forecast
# (ein konsistenter 30-Tage-Verlauf für Dashboard & DB), plus getrennte CSVs
# für die Evaluation der beiden Läufe und ein Stunden-Forecast für die
# Schichtplanung (Top-Down-Disaggregation, siehe hourly_profile.py).

import os
import time
from datetime import date, timedelta

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from futureexpert import ExpertClient
from futureexpert.checkin import (
    DataDefinition, DateColumn, ValueColumn, TsCreationConfig
)
from futureexpert.forecast import ReportConfig, ForecastingConfig, PreprocessingConfig
from futureexpert.matcher import LagSelectionConfig, MatcherConfig

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forecast_db import write_predictions, write_staffing_recommendations  # noqa: E402
from hourly_profile import disaggregate, load_profile  # noqa: E402
from weather_forecast import get_weather_future  # noqa: E402

# ── KONFIGURATION ─────────────────────────────────────────────────────────────
load_dotenv()
HORIZON_DETAIL = 10   # genauer Forecast mit Wetter-Kovariaten
HORIZON_COARSE = 30   # grober Forecast, univariat

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 0. VORAB-CHECKS (klare Meldungen statt langer Tracebacks) ────────────────
if os.environ.get("FUTURE_USER", "").strip() in ("", "dein-benutzername"):
    raise SystemExit(
        "FEHLER: FUTURE_USER / FUTURE_PW fehlen in der .env – ohne\n"
        "        futureEXPERT-Zugang (prognostica-Account) kann dieses Skript\n"
        "        nicht laufen. Alternative ohne Account:\n"
        '        python "models(Nico)/ml_forecast.py"'
    )


def connect_engine():
    """
    Verbindet zur Neon-DB: bevorzugt DATABASE_URL_DS (darf gold schreiben),
    fällt bei Verbindungs-/Login-Fehlern automatisch auf DATABASE_URL_ETL
    zurück (kann raw lesen; gold-Write wird dann übersprungen statt abzubrechen).
    """
    for name in ("DATABASE_URL_DS", "DATABASE_URL_ETL"):
        url = os.environ.get(name)
        if not url or "ep-xxx" in url:
            continue
        eng = create_engine(url, pool_pre_ping=True)
        try:
            with eng.connect() as c:
                c.execute(text("SELECT 1"))
            print(f"  Verbunden über {name}")
            return eng
        except Exception as exc:
            print(f"  WARN: {name} nicht nutzbar ({str(exc)[:90]})")
    raise SystemExit(
        "FEHLER: Keine der Datenbank-URLs aus der .env funktioniert.\n"
        "        Bitte URLs prüfen (Host/Passwort) – siehe .env im Projektroot."
    )


# ── 1. DATEN AUS NEON DB LADEN ────────────────────────────────────────────────
print("Verbinde mit Neon DB...")
engine = connect_engine()

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

# Aktualitäts-Check: Der Forecast startet am Tag nach dem letzten Datenpunkt.
# Sind die Daten alt, prognostiziert man die Vergangenheit.
_last_day = visitors_daily["datum"].max().date()
if _last_day < date.today() - timedelta(days=1):
    print(f"\n  WARN: Besucherdaten enden am {_last_day} – der Forecast beginnt dort,"
          f"\n        nicht heute! Für einen aktuellen Forecast zuerst die"
          f"\n        ETL-Pipeline laufen lassen:  python -m etl.pipeline")


# ── 3. EIGENEN WETTER-FORECAST HOLEN (Zukunfts-Kovariate) ────────────────────
# Kovariaten brauchen Werte IM Prognosezeitraum. Dafür liefert
# weather_forecast.py eine echte Wettervorhersage (Open-Meteo) für die
# nächsten HORIZON_DETAIL Tage, die an die Wetter-Historie angehängt wird.
print("\nHole Wetter-Forecast (Open-Meteo)...")
weather_future = get_weather_future(HORIZON_DETAIL)
print(weather_future.to_string(index=False))

weather_extended = pd.concat([
    weather_daily,
    weather_future[["datum", "temperature_c", "precipitation_mm"]],
], ignore_index=True).drop_duplicates(subset="datum", keep="first")


# ── 4. FUTUREEXPERT LOGIN ─────────────────────────────────────────────────────
print("\nLogge ein bei futureEXPERT...")
client = ExpertClient.from_user_password()


# ── 5. CHECK-IN BESUCHER-ZEITREIHE ───────────────────────────────────────────
print("\nCHECK-IN Besucherdaten...")

visitors_csv = os.path.join(BASE_DIR, "visitors_daily.csv")
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


# ── 6. CHECK-IN WETTER ALS KOVARIATE (Historie + Forecast) ───────────────────
print("\nCHECK-IN Wetterdaten als Kovariate (inkl. Wetter-Forecast)...")

weather_csv = os.path.join(BASE_DIR, "weather_daily.csv")
weather_extended.to_csv(weather_csv, index=False, date_format="%Y-%m-%d")

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


# ── HILFSFUNKTIONEN ──────────────────────────────────────────────────────────

def wait_for_report(report_id) -> None:
    """Pollt den Report-Status bis der Lauf abgeschlossen ist."""
    print("  Warte auf Ergebnis", end="", flush=True)
    while True:
        status = client.get_report_status(id=report_id)
        if status.is_finished:
            print(" ✓")
            return
        print(".", end="", flush=True)
        time.sleep(10)


def results_to_df(results) -> tuple[pd.DataFrame, str]:
    """Bestes Modell eines Forecast-Reports als DataFrame (datum/forecast/low/high)."""
    for fc in results.forecast_results:
        best = fc.best_model
        if best is None:
            continue
        df = pd.DataFrame([{
            "datum":    v.time_stamp_utc,
            "forecast": v.point_forecast_value,
            "low":      v.lower_limit_value,
            "high":     v.upper_limit_value,
        } for v in best.forecasts])
        used_covs = ", ".join(c.ts.name for c in (best.covariates or [])) or "keine"
        print(f"  Modell: {best.model_name} | Kovariaten: {used_covs}")
        return df, str(best.model_name)
    raise RuntimeError("futureEXPERT hat kein Modell geliefert.")


# ── 7. MATCHER: PRÜFT NUTZEN DER WETTER-KOVARIATEN ───────────────────────────
# Der Matcher bewertet, ob (und mit welchem Lag) die Kovariaten die Prognose
# verbessern. Lag 0 ist fixiert, weil unser Wetter-Forecast die Zukunftswerte
# taggenau liefert. Schlägt der Matcher fehl, läuft der Detail-Forecast
# univariat weiter (Fallback statt Abbruch).
matcher_report_id = None
try:
    print("\nStarte MATCHER (Kovariaten-Auswahl)...")
    matcher_id = client.start_matcher(config=MatcherConfig(
        title="Besucher x Wetter (Kovariaten-Check)",
        actuals_version=version_visitors,
        covs_versions=[version_weather],
        lag_selection=LagSelectionConfig(fixed_lags=[0]),
    ))
    wait_for_report(matcher_id)
    matcher_results = client.get_matcher_results(id=matcher_id)
    for res in matcher_results:
        for detail in res.ranking:
            covs = ", ".join(c.ts.name for c in detail.covariates) or "(ohne Kovariate)"
            print(f"  Rang {detail.rank}: {covs}")
    matcher_report_id = matcher_id.report_id
except Exception as exc:
    print(f"  WARN: Matcher fehlgeschlagen ({exc}) – Detail-Forecast läuft univariat.")


# ── 8. FORECASTS STARTEN (10 Tage Detail + 30 Tage Grob) ─────────────────────
preprocessing = PreprocessingConfig(
    detect_outliers=True,
    replace_outliers=True,
    detect_changepoints=True,
)

print(f"\nStarte DETAIL-FORECAST ({HORIZON_DETAIL} Tage, mit Wetter)...")
detail_config = ReportConfig(
    title=f"Bibliothek Hubland – Detail {HORIZON_DETAIL} Tage (Wetter-Kovariaten)",
    forecasting=ForecastingConfig(
        fc_horizon=HORIZON_DETAIL,
        lower_bound=0.0,
        round_forecast_to_integer=True,
    ),
    preprocessing=preprocessing,
    matcher_report_id=matcher_report_id,
    covs_versions=[version_weather] if matcher_report_id is not None else [],
)
detail_report = client.start_forecast(version=version_visitors, config=detail_config)
print(f"  Report ID: {detail_report.report_id}")

print(f"\nStarte GROB-FORECAST ({HORIZON_COARSE} Tage, univariat)...")
coarse_config = ReportConfig(
    title=f"Bibliothek Hubland – Grob {HORIZON_COARSE} Tage",
    forecasting=ForecastingConfig(
        fc_horizon=HORIZON_COARSE,
        lower_bound=0.0,
        round_forecast_to_integer=True,
    ),
    preprocessing=preprocessing,
)
coarse_report = client.start_forecast(version=version_visitors, config=coarse_config)
print(f"  Report ID: {coarse_report.report_id}")


# ── 9. AUF ERGEBNISSE WARTEN & LADEN ─────────────────────────────────────────
print("\nDETAIL-FORECAST:")
wait_for_report(detail_report)
detail_results = client.get_fc_results(
    id=detail_report, include_k_best_models=1, include_backtesting=True
)
detail_df, detail_model = results_to_df(detail_results)

print("\nGROB-FORECAST:")
wait_for_report(coarse_report)
coarse_results = client.get_fc_results(
    id=coarse_report, include_k_best_models=1, include_backtesting=True
)
coarse_df, coarse_model = results_to_df(coarse_results)


# ── 10. HORIZONTE KOMBINIEREN & PLAUSIBILITÄT PRÜFEN ─────────────────────────
# Tag 1–10 aus dem Detail-Lauf (Wetter), Tag 11–30 aus dem Grob-Lauf.
detail_df["datum"] = pd.to_datetime(detail_df["datum"])
coarse_df["datum"] = pd.to_datetime(coarse_df["datum"])

blended = pd.concat([
    detail_df,
    coarse_df[~coarse_df["datum"].isin(detail_df["datum"])],
]).sort_values("datum").reset_index(drop=True)

# Plausibilitätscheck gegen die Historie (bewusst großzügige Grenzen –
# soll nur grobe Ausreißer/Modellfehler abfangen, keine echten Trends).
hist_mean = float(visitors_daily["besucher"].mean())
hist_max = float(visitors_daily["besucher"].max())
fc_mean = float(blended["forecast"].mean())
if fc_mean > 2 * hist_mean or float(blended["forecast"].max()) > 3 * hist_max:
    print(f"  WARN: Prognose auffällig hoch (Ø {fc_mean:.0f} vs. historisch "
          f"Ø {hist_mean:.0f}) – bitte Lauf prüfen!")
if fc_mean < 0.3 * hist_mean:
    print(f"  WARN: Prognose auffällig niedrig (Ø {fc_mean:.0f} vs. historisch "
          f"Ø {hist_mean:.0f}) – bitte Lauf prüfen!")


# ── 11. TAGES-CSVs SPEICHERN ─────────────────────────────────────────────────
detail_path = os.path.join(BASE_DIR, "forecast_besucher_10d.csv")
coarse_path = os.path.join(BASE_DIR, "forecast_besucher_30d.csv")
blended_path = os.path.join(BASE_DIR, "forecast_besucher.csv")  # liest das Dashboard

detail_df.to_csv(detail_path, index=False)
coarse_df.to_csv(coarse_path, index=False)
blended.to_csv(blended_path, index=False)

print(f"\nDetail ({HORIZON_DETAIL} Tage, Modell {detail_model}):")
print(detail_df.to_string(index=False))
print(f"\nKombiniert gespeichert: {blended_path}")


# ── 12. STUNDEN-FORECAST (für die Schicht-/Personalplanung) ──────────────────
# Tagesprognose × empirisches Stundenprofil je Wochentag, gelernt aus der
# echten stündlichen Besucherhistorie (Top-Down-Disaggregation). Die Stunden-
# summen eines Tages ergeben exakt die Tagesprognose.
print("\nErzeuge Stunden-Forecast (Wochentagsprofil aus Historie)...")
profile = load_profile(engine)
hourly_fc = disaggregate(blended, profile)

hourly_path = os.path.join(BASE_DIR, "forecast_besucher_stuendlich.csv")
hourly_fc.to_csv(hourly_path, index=False)
print(f"  {len(hourly_fc)} Stundenwerte über {HORIZON_COARSE} Tage")
print(f"  Gespeichert: {hourly_path}")

first_day = hourly_fc["timestamp_local"].iloc[0].date()
print(f"\n  Beispiel {first_day}:")
mask = hourly_fc["timestamp_local"].dt.date == first_day
print(hourly_fc[mask].to_string(index=False))


# ── 13. IN DIE NEON DB SCHREIBEN ─────────────────────────────────────────────
model_version = f"detail:{detail_model}|grob:{coarse_model}"[:100]
print("\nSchreibe Prognose in NeonDB...")
try:
    write_predictions(blended, model_name="futureEXPERT", model_version=model_version)
    write_staffing_recommendations(blended, model_version=model_version,
                                   hourly_profile=profile)
except Exception as exc:  # DB darf den Lauf nicht abbrechen – CSV bleibt erhalten
    print(f"  WARN: DB-Write fehlgeschlagen ({exc}). CSV-Ausgabe bleibt nutzbar.")

print("\nFertig!")
