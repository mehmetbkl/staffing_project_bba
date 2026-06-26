"""
callbacks/chart_callbacks.py
Chart-Update bei jedem Wetter-Refresh.
"""

from __future__ import annotations
import logging
from dash import Input, Output
from layouts.forecast_chart import build_forecast_figure
from services.forecast_service import get_placeholder_forecast

logger = logging.getLogger(__name__)


def register_chart_callbacks(app) -> None:

    @app.callback(
        Output("forecast-graph", "figure"),
        Input("weather-interval", "n_intervals"),
    )
    def update_chart(n_intervals: int):
        logger.info("Chart-Update #%d", n_intervals)
        forecast = get_placeholder_forecast()
        return build_forecast_figure([
            {
                "hour_label":         p.timestamp.strftime("%H:%M"),
                "predicted_visitors": p.predicted_visitors,
                "recommended_staff":  p.recommended_staff,
                "confidence_low":     p.confidence_low,
                "confidence_high":    p.confidence_high,
            }
            for p in forecast.points
        ])