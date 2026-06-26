"""
layouts/weather_widget.py
Wetter-Widget: Live-Daten von Open-Meteo + Stundenvorschau.
"""

from __future__ import annotations
import logging
from dash import dcc, html
from utils.formatting import (
    format_cloud_cover, format_precipitation,
    format_temperature, format_wind_speed,
)

logger = logging.getLogger(__name__)


def render_weather_loading() -> html.Div:
    return html.Div(
        className="weather-loading",
        children=[html.Div(className="spinner"), "Wetterdaten werden geladen..."],
    )


def render_weather_error(message: str = "Wetterdaten nicht verfügbar") -> html.Div:
    return html.Div(
        className="weather-error",
        children=[
            html.Span("error_outline", className="material-symbols-outlined"),
            message,
        ],
    )


def render_weather_content(weather_data: dict | None) -> html.Div:
    if weather_data is None:
        return render_weather_error()

    icon  = weather_data.get("icon", "cloud")
    desc  = weather_data.get("description", "–")
    temp  = weather_data.get("temperature_c")
    prec  = weather_data.get("precipitation_mm")
    wind  = weather_data.get("wind_speed_kmh")
    cloud = weather_data.get("cloud_cover_pct")

    forecast_items = [
        html.Div(
            className=(
                "weather-forecast-item weather-forecast-item--active"
                if p.get("is_now") else "weather-forecast-item"
            ),
            children=[
                html.Span(
                    p.get("icon", "cloud"),
                    className="material-symbols-outlined",
                    style={"fontSize": "16px"},
                ),
                html.Div(p.get("hour_label", ""), style={"fontSize": "10px"}),
                html.Div(
                    format_temperature(p.get("temperature_c"), "°"),
                    className="weather-forecast-temp",
                ),
            ],
        )
        for p in weather_data.get("forecast", [])[:6]
    ]

    return html.Div([
        html.Div(
            className="weather-main",
            children=[
                html.Div(
                    className="weather-icon-wrap",
                    children=html.Span(
                        icon,
                        className="material-symbols-outlined fill",
                        style={"fontSize": "32px"},
                    ),
                ),
                html.Div([
                    html.Div(format_temperature(temp), className="weather-temp"),
                    html.Div(desc, className="weather-desc"),
                ]),
            ],
        ),
        html.Div(
            className="weather-detail-row",
            children=[
                html.Div(className="weather-detail-item", children=[
                    html.Div("Wind", className="weather-detail-label"),
                    html.Div(format_wind_speed(wind), className="weather-detail-value"),
                ]),
                html.Div(className="weather-detail-item", children=[
                    html.Div("Regen", className="weather-detail-label"),
                    html.Div(format_precipitation(prec), className="weather-detail-value"),
                ]),
                html.Div(className="weather-detail-item", children=[
                    html.Div("Bewölkung", className="weather-detail-label"),
                    html.Div(format_cloud_cover(cloud), className="weather-detail-value"),
                ]),
            ],
        ),
        html.Div(className="weather-forecast-row", children=forecast_items)
        if forecast_items else html.Div(),
    ])


def render_weather_widget() -> html.Div:
    from utils.constants import WEATHER_REFRESH_INTERVAL_MS
    return html.Div(
        className="card",
        children=[
            html.Div(
                className="card__header",
                children=[
                    html.Span(
                        "cloud",
                        className="material-symbols-outlined card__header-icon",
                    ),
                    "Externe Faktoren",
                ],
            ),
            html.Div(
                id="weather-widget-content",
                children=render_weather_loading(),
            ),
            dcc.Interval(
                id="weather-interval",
                interval=WEATHER_REFRESH_INTERVAL_MS,
                n_intervals=0,
            ),
        ],
    )