"""
callbacks/chart_callbacks.py
Chart-Update bei jedem Wetter-Refresh sowie Neu-Einfärben aller Charts
(Prognose + Historie) beim Hell-/Dunkelmodus-Wechsel.
"""

from __future__ import annotations
import logging
from dash import Input, Output
from layouts.forecast_chart import build_forecast_figure
from services.forecast_service import get_forecast

logger = logging.getLogger(__name__)


def register_chart_callbacks(app) -> None:

    @app.callback(
        Output("forecast-graph", "figure"),
        Input("weather-interval", "n_intervals"),
        Input("theme-store", "data"),   # neu zeichnen bei Theme-Wechsel
    )
    def update_chart(n_intervals: int, theme: str | None):
        theme = theme if theme in ("light", "dark") else "light"
        logger.info("Chart-Update #%d (theme=%s)", n_intervals, theme)
        forecast = get_forecast()
        return build_forecast_figure(
            [
                {
                    "hour_label":         p.timestamp.strftime("%H:%M"),
                    "predicted_visitors": p.predicted_visitors,
                    "recommended_staff":  p.recommended_staff,
                    "confidence_low":     p.confidence_low,
                    "confidence_high":    p.confidence_high,
                }
                for p in forecast.points
            ],
            theme=theme,
        )

    # ── Historie-Charts beim Theme-Wechsel neu einfärben ─────────────────────
    # Die vier Historie-Diagramme werden nur beim Seitenaufruf gerendert und
    # bekamen das Theme bisher nicht mit, wenn man auf der Seite umschaltete.
    # Dieser Callback baut sie bei jeder theme-store-Änderung neu.
    # suppress_callback_exceptions=True (app.py) sorgt dafür, dass der Callback
    # ins Leere läuft, solange die Historie-Seite nicht aktiv ist.
    from layouts.history_page import HISTORY_FIGURES, build_history_figures

    @app.callback(
        [Output(graph_id, "figure") for graph_id in HISTORY_FIGURES],
        Input("theme-store", "data"),
        prevent_initial_call=True,
    )
    def update_history_charts(theme: str | None):
        theme = theme if theme in ("light", "dark") else "light"
        logger.info("Historie-Charts neu einfärben (theme=%s)", theme)
        return build_history_figures(theme)