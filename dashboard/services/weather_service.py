"""
services/weather_service.py
Open-Meteo-Anbindung. Basiert auf dem bestehenden ETL-Code.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests

from utils.constants import (
    DEFAULT_WEATHER_DESC, DEFAULT_WEATHER_ICON,
    LIBRARY_LAT, LIBRARY_LON,
    WEATHER_BASE_URL, WEATHER_FORECAST_URL,
    WEATHER_START_DATE, WEATHER_TIMEZONE,
    WMO_CODE_MAP,
)

logger = logging.getLogger(__name__)


@dataclass
class CurrentWeather:
    timestamp: datetime
    temperature_c: float
    precipitation_mm: float
    weather_code: int
    wind_speed_kmh: float
    cloud_cover_pct: float

    @property
    def icon(self) -> str:
        return WMO_CODE_MAP.get(self.weather_code, (DEFAULT_WEATHER_ICON, ""))[0]

    @property
    def description(self) -> str:
        return WMO_CODE_MAP.get(self.weather_code, ("", DEFAULT_WEATHER_DESC))[1]


@dataclass
class HourlyForecastPoint:
    timestamp: datetime
    temperature_c: float
    weather_code: int
    precipitation_mm: float

    @property
    def icon(self) -> str:
        return WMO_CODE_MAP.get(self.weather_code, (DEFAULT_WEATHER_ICON, ""))[0]

    @property
    def hour_label(self) -> str:
        return self.timestamp.strftime("%H:%M")


def _parse_hourly_df(data: dict) -> pd.DataFrame:
    hourly = data["hourly"]
    return pd.DataFrame({
        "timestamp_local":  pd.to_datetime(hourly["time"]),
        "temperature_c":    hourly["temperature_2m"],
        "precipitation_mm": hourly["precipitation"],
        "weather_code":     hourly["weather_code"],
        "wind_speed_kmh":   hourly["wind_speed_10m"],
        "cloud_cover_pct":  hourly["cloud_cover"],
    })


def fetch_historical(start_date: str = WEATHER_START_DATE) -> pd.DataFrame:
    """Historische Stundendaten – identisch mit ETL fetch_all()."""
    today = pd.Timestamp.now().strftime("%Y-%m-%d")
    params = {
        "latitude": LIBRARY_LAT, "longitude": LIBRARY_LON,
        "start_date": start_date, "end_date": today,
        "hourly": "temperature_2m,precipitation,weather_code,wind_speed_10m,cloud_cover",
        "timezone": WEATHER_TIMEZONE,
    }
    logger.info("Lade historische Wetterdaten %s -> %s", start_date, today)
    r = requests.get(WEATHER_BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    return _parse_hourly_df(r.json())


def fetch_current_weather() -> Optional[CurrentWeather]:
    """Aktueller Stundenwert via Forecast-API."""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    params = {
        "latitude": LIBRARY_LAT, "longitude": LIBRARY_LON,
        "start_date": today.isoformat(), "end_date": tomorrow.isoformat(),
        "hourly": "temperature_2m,precipitation,weather_code,wind_speed_10m,cloud_cover",
        "timezone": WEATHER_TIMEZONE,
    }
    try:
        r = requests.get(WEATHER_FORECAST_URL, params=params, timeout=15)
        r.raise_for_status()
        df = _parse_hourly_df(r.json())
        now = pd.Timestamp.now()
        df["_diff"] = (df["timestamp_local"] - now).abs()
        row = df.nsmallest(1, "_diff").iloc[0]
        return CurrentWeather(
            timestamp=row["timestamp_local"].to_pydatetime(),
            temperature_c=float(row["temperature_c"]),
            precipitation_mm=float(row["precipitation_mm"]),
            weather_code=int(row["weather_code"]),
            wind_speed_kmh=float(row["wind_speed_kmh"]),
            cloud_cover_pct=float(row["cloud_cover_pct"]),
        )
    except Exception as exc:
        logger.error("Fehler beim Wetter-Abruf: %s", exc)
        return None


def fetch_hourly_forecast(hours: int = 8) -> list[HourlyForecastPoint]:
    """Stundenvorhersage für die nächsten `hours` Stunden."""
    today = datetime.now().date()
    params = {
        "latitude": LIBRARY_LAT, "longitude": LIBRARY_LON,
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=2)).isoformat(),
        "hourly": "temperature_2m,precipitation,weather_code",
        "timezone": WEATHER_TIMEZONE,
    }
    try:
        r = requests.get(WEATHER_FORECAST_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()["hourly"]
        now = datetime.now()
        points: list[HourlyForecastPoint] = []
        for ts, temp, code, prec in zip(
            data["time"], data["temperature_2m"],
            data["weather_code"], data["precipitation"],
        ):
            dt = datetime.fromisoformat(ts)
            if dt >= now:
                points.append(HourlyForecastPoint(
                    timestamp=dt, temperature_c=float(temp),
                    weather_code=int(code), precipitation_mm=float(prec),
                ))
            if len(points) >= hours:
                break
        return points
    except Exception as exc:
        logger.error("Fehler beim Forecast-Abruf: %s", exc)
        return []