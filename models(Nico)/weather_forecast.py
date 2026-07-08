"""
models(Nico)/weather_forecast.py
Eigener Wetter-Forecast als Zukunfts-Kovariate für den Besucher-Forecast.

Warum ein eigener Wetter-Forecast?
----------------------------------
Der Besucher-Forecast nutzt Temperatur und Niederschlag als Kovariaten. Für
Prognosetage in der Zukunft braucht das Modell dafür Wetter-*Prognosen* statt
historischer Werte. Quelle ist die Open-Meteo Forecast-API – dieselbe Quelle
wie die historischen Wetterdaten in raw.weather (konsistente Messbasis, offene
Lizenz, kein API-Key nötig). wetter.de bietet keine öffentliche API und wurde
deshalb verworfen.

Zwei Reichweiten (bewusst getrennt, weil Wettermodelle nur ~14 Tage
Vorhersagekraft haben):
  * Tag 1–16:   numerische Wettervorhersage (Open-Meteo Forecast-API)
  * Tag 17–H:   Klimatologie – mehrjähriger Mittelwert je Kalendertag
                (±7-Tage-Fenster) aus dem Open-Meteo-Archiv. Jenseits des
                Vorhersagehorizonts ist der klimatologische Erwartungswert
                der methodisch saubere Ersatz für eine Punktvorhersage.

Die Spalte `source` kennzeichnet je Tag die Herkunft ("forecast" |
"climatology" | "persistence"-Fallback), damit die Datenherkunft im
Modell-Report transparent bleibt.

Aufruf (Standalone-Test, schreibt weather_forecast.csv):
    python "models(Nico)/weather_forecast.py"
"""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()
LIBRARY_LAT: float = float(os.environ.get("LIBRARY_LAT", 49.7806))
LIBRARY_LON: float = float(os.environ.get("LIBRARY_LON", 9.9718))

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEZONE = "Europe/Berlin"
MAX_NWP_DAYS = 15
CLIMATOLOGY_YEARS = 10     # Referenzzeitraum für die Klimatologie
CLIMATOLOGY_WINDOW = 7     # ±Tage um den Kalendertag (glättet Einzeljahre)


def _hourly_to_daily(data: dict) -> pd.DataFrame:
    """
    Aggregiert eine Open-Meteo-Stundenantwort auf Tageswerte – identisch zur
    Aggregation der Wetter-Historie im Forecast-Skript (Mittel der Temperatur,
    Summe des Niederschlags), damit Kovariaten-Historie und -Zukunft dieselbe
    Messgröße sind.
    """
    hourly = data["hourly"]
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(hourly["time"]),
        "temperature_c": hourly["temperature_2m"],
        "precipitation_mm": hourly["precipitation"],
    }).dropna()
    out = (
        df.groupby(df["timestamp"].dt.date)
        .agg(temperature_c=("temperature_c", "mean"),
             precipitation_mm=("precipitation_mm", "sum"))
        .reset_index()
        .rename(columns={"timestamp": "datum"})
    )
    out["datum"] = pd.to_datetime(out["datum"])
    out["temperature_c"] = out["temperature_c"].round(1)
    out["precipitation_mm"] = out["precipitation_mm"].round(2)
    return out


def fetch_open_meteo_forecast(days: int) -> pd.DataFrame:
    """
    Numerische Wettervorhersage (Tagesauflösung) für die nächsten `days` Tage.

    Nutzt dieselben Stunden-Variablen wie dashboard/services/weather_service.py
    und aggregiert selbst auf Tageswerte. Returns DataFrame mit Spalten:
    datum, temperature_c, precipitation_mm, source="forecast".
    Beginnt bei morgen (heute ist kein Prognosetag).
    """
    days = min(days, MAX_NWP_DAYS)
    params = {
        "latitude": LIBRARY_LAT,
        "longitude": LIBRARY_LON,
        "hourly": "temperature_2m,precipitation",
        "timezone": TIMEZONE,
        "forecast_days": min(days + 1, 16),
    }
    r = requests.get(FORECAST_URL, params=params, timeout=30)
    r.raise_for_status()

    df = _hourly_to_daily(r.json())
    df = df[df["datum"].dt.date > date.today()].head(days).reset_index(drop=True)
    df["source"] = "forecast"
    return df


def fetch_climatology(target_dates: list[date],
                      years: int = CLIMATOLOGY_YEARS) -> pd.DataFrame:
    """
    Klimatologischer Erwartungswert je Zieldatum: Mittel über `years` Jahre
    in einem ±CLIMATOLOGY_WINDOW-Tage-Fenster um den Kalendertag.

    Returns DataFrame mit Spalten: datum, temperature_c, precipitation_mm,
    source="climatology".
    """
    if not target_dates:
        return pd.DataFrame(
            columns=["datum", "temperature_c", "precipitation_mm", "source"]
        )

    end = date.today() - timedelta(days=6)  # Archiv hat wenige Tage Verzug
    start = end.replace(year=end.year - years)
    params = {
        "latitude": LIBRARY_LAT,
        "longitude": LIBRARY_LON,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "hourly": "temperature_2m,precipitation",  # wie etl/sources/weather.py
        "timezone": TIMEZONE,
    }
    r = requests.get(ARCHIVE_URL, params=params, timeout=60)
    r.raise_for_status()

    hist = _hourly_to_daily(r.json())
    hist["doy"] = hist["datum"].dt.dayofyear

    rows: list[dict] = []
    for d in target_dates:
        doy = pd.Timestamp(d).dayofyear
        # zyklische Distanz im Kalenderjahr (Jahreswechsel-sicher)
        dist = (hist["doy"] - doy).abs()
        dist = pd.concat([dist, 365 - dist], axis=1).min(axis=1)
        window = hist[dist <= CLIMATOLOGY_WINDOW]
        rows.append({
            "datum": pd.Timestamp(d),
            "temperature_c": round(float(window["temperature_c"].mean()), 1),
            "precipitation_mm": round(float(window["precipitation_mm"].mean()), 2),
            "source": "climatology",
        })
    return pd.DataFrame(rows)


def get_weather_future(horizon_days: int) -> pd.DataFrame:
    """
    Kombinierter Wetter-Forecast für die nächsten `horizon_days` Tage
    (ab morgen): Tag 1–16 Vorhersage, danach Klimatologie.

    Fällt die Forecast-API aus, wird komplett auf Klimatologie ausgewichen;
    fällt auch das Archiv aus, wird der letzte bekannte Wert fortgeschrieben
    (Persistenz) – der Besucher-Forecast bricht dadurch nie ab.
    """
    tomorrow = date.today() + timedelta(days=1)
    all_dates = [tomorrow + timedelta(days=i) for i in range(horizon_days)]

    try:
        nwp = fetch_open_meteo_forecast(horizon_days)
    except Exception as exc:
        logger.warning("Open-Meteo Forecast-API nicht erreichbar (%s) – "
                       "weiche auf Klimatologie aus.", exc)
        nwp = pd.DataFrame(
            columns=["datum", "temperature_c", "precipitation_mm", "source"]
        )

    covered = set(nwp["datum"].dt.date) if not nwp.empty else set()
    missing = [d for d in all_dates if d not in covered]

    parts = [nwp]
    if missing:
        try:
            parts.append(fetch_climatology(missing))
        except Exception as exc:
            logger.warning("Klimatologie nicht verfügbar (%s) – "
                           "Persistenz-Fallback.", exc)
            if not nwp.empty:
                last = nwp.iloc[-1]
                t, p = float(last["temperature_c"]), float(last["precipitation_mm"])
            else:  # gar keine Wetterdaten erreichbar
                t, p = 15.0, 1.5
            parts.append(pd.DataFrame([{
                "datum": pd.Timestamp(d), "temperature_c": t,
                "precipitation_mm": p, "source": "persistence",
            } for d in missing]))

    parts = [p for p in parts if not p.empty]
    out = (
        pd.concat(parts, ignore_index=True)
        .sort_values("datum")
        .reset_index(drop=True)
    )
    # Sanity-Checks: keine Lücken, keine negativen Niederschläge
    assert len(out) == horizon_days, (
        f"Wetter-Forecast unvollständig: {len(out)}/{horizon_days} Tage"
    )
    out["precipitation_mm"] = out["precipitation_mm"].clip(lower=0)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fc = get_weather_future(30)
    print("Wetter-Forecast (30 Tage, ab morgen):")
    print(fc.to_string(index=False))
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "weather_forecast.csv")
    fc.to_csv(out_path, index=False, date_format="%Y-%m-%d")
    print(f"\nGespeichert: {out_path}")
