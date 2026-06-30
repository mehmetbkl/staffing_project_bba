"""
callbacks/weather_callbacks.py
Kein prevent_initial_call → feuert sofort beim ersten Load.
"""

from __future__ import annotations
import logging
from datetime import datetime
from dash import Input, Output
from layouts.weather_widget import render_weather_content, render_weather_error
from services.weather_service import fetch_current_weather, fetch_hourly_forecast

logger = logging.getLogger(__name__)


def register_weather_callbacks(app) -> None:

    @app.callback(
        Output("weather-widget-content", "children"),
        Input("weather-interval", "n_intervals"),
    )
    def update_weather(n_intervals: int):
        logger.info("Wetter-Update #%d", n_intervals)
        current = fetch_current_weather()
        if current is None:
            return render_weather_error("Open-Meteo nicht erreichbar")

        now = datetime.now()
        forecast_pts = fetch_hourly_forecast(hours=8)
        serialized = [
            {
                "hour_label":    p.hour_label,
                "temperature_c": p.temperature_c,
                "icon":          p.icon,
                "is_now":        abs((p.timestamp - now).total_seconds() / 60) < 35,
            }
            for p in forecast_pts[:6]
        ]
        logger.info("Wetter: %.1f°C, %s", current.temperature_c, current.description)
        return render_weather_content({
            "icon":             current.icon,
            "description":      current.description,
            "temperature_c":    current.temperature_c,
            "precipitation_mm": current.precipitation_mm,
            "wind_speed_kmh":   current.wind_speed_kmh,
            "cloud_cover_pct":  current.cloud_cover_pct,
            "forecast":         serialized,
        })