import requests
import pandas as pd
from etl.config import LIBRARY_LAT, LIBRARY_LON

START_DATE = "2025-04-24"
BASE_URL   = "https://archive-api.open-meteo.com/v1/archive"

def fetch_all():
    today  = pd.Timestamp.now().strftime("%Y-%m-%d")
    params = {
        "latitude":  LIBRARY_LAT,
        "longitude": LIBRARY_LON,
        "start_date": START_DATE,
        "end_date":   today,
        "hourly": "temperature_2m,precipitation,weather_code,wind_speed_10m,cloud_cover",
        "timezone": "Europe/Berlin",
    }
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()["hourly"]

    df = pd.DataFrame({
        "timestamp_local": pd.to_datetime(data["time"]),
        "temperature_c":   data["temperature_2m"],
        "precipitation_mm": data["precipitation"],
        "weather_code":    data["weather_code"],
        "wind_speed_kmh":  data["wind_speed_10m"],
        "cloud_cover_pct": data["cloud_cover"],
    })
    return df

if __name__ == "__main__":
    df = fetch_all()
    from etl.loaders.postgres import load_weather
    load_weather(df)