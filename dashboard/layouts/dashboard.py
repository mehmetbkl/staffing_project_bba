"""
layouts/dashboard.py
App-Shell mit dcc.Location-Routing.
/ → Dashboard-Seite    /prognose → Prognose-Seite
"""

from __future__ import annotations
from dash import dcc, html

from layouts.forecast_chart import render_forecast_chart
from layouts.navbar import render_navbar
from layouts.sidebar import render_sidebar
from layouts.staffing_actions import derive_actions_from_forecast, render_staffing_actions
from layouts.summary_widget import render_summary_widget
from layouts.weather_widget import render_weather_widget
from services.forecast_service import get_placeholder_forecast
from utils.formatting import format_date_de


def _to_points(forecast) -> list[dict]:
    return [
        {
            "hour_label":         p.timestamp.strftime("%H:%M"),
            "predicted_visitors": p.predicted_visitors,
            "recommended_staff":  p.recommended_staff,
            "confidence_low":     p.confidence_low,
            "confidence_high":    p.confidence_high,
        }
        for p in forecast.points
    ]


def render_prognose_page() -> html.Div:
    """
    Prognose-Seite.
    Wetter: Live via Callback (Open-Meteo API).
    Chart + Maßnahmen: aus Prognose (Platzhalter → wird durch ANN ersetzt).
    """
    forecast = get_placeholder_forecast()
    points   = _to_points(forecast)
    actions  = derive_actions_from_forecast(points)

    return html.Div([
        html.Div(
            className="page-header",
            children=[html.Div([
                html.H2("Nachfrageprognose", className="page-header__title"),
                html.P(
                    format_date_de() + " · Hubland, Würzburg",
                    className="page-header__subtitle",
                ),
            ])],
        ),
        html.Div(
            className="bento-grid",
            children=[
                html.Div(
                    className="bento-col-left",
                    children=[
                        render_weather_widget(),
                        render_summary_widget(
                            predicted_traffic=forecast.predicted_traffic,
                            recommended_hours=forecast.recommended_hours,
                            traffic_change_pct=forecast.traffic_change_pct,
                        ),
                    ],
                ),
                html.Div(
                    className="bento-col-right",
                    children=[
                        render_forecast_chart(),
                        render_staffing_actions(actions),
                    ],
                ),
            ],
        ),
    ])


def render_dashboard_page() -> html.Div:
    """
    Dashboard-Seite.
    Alle KPI-Werte kommen aus der Prognose – kein einziger Wert hardcodiert.
    """
    forecast = get_placeholder_forecast()
    points   = _to_points(forecast)

    peak = max(points, key=lambda p: p["predicted_visitors"]) if points else {}
    understaffed = sum(
        1 for p in points
        if p["predicted_visitors"] > 80 and p["recommended_staff"] < 4
    )
    change = forecast.traffic_change_pct
    change_str = (
        f"{'+' if change >= 0 else ''}{change:.0f} % vs. gestern"
        if change is not None else "–"
    )

    return html.Div([
        html.Div(
            className="page-header",
            children=[html.Div([
                html.H2("Dashboard", className="page-header__title"),
                html.P(
                    format_date_de() + " · Hubland, Würzburg",
                    className="page-header__subtitle",
                ),
            ])],
        ),
        html.Div(
            className="dashboard-kpi-grid",
            children=[
                _kpi(
                    "Besucher heute",
                    str(forecast.predicted_traffic),
                    "person",
                    change_str,
                    "negative" if change and change < 0 else "neutral",
                ),
                _kpi(
                    "Empf. Stunden",
                    f"{forecast.recommended_hours:.0f} h",
                    "schedule",
                    "Summe Personalstunden",
                    "neutral",
                ),
                _kpi(
                    "Peak-Stunde",
                    peak.get("hour_label", "–"),
                    "trending_up",
                    f"{peak.get('recommended_staff', '–')} Mitarbeiter empfohlen",
                    "neutral",
                ),
                _kpi(
                    "Unterbes. Stunden",
                    str(understaffed),
                    "warning",
                    "Prüfung in Prognose empfohlen",
                    "warning" if understaffed > 0 else "neutral",
                ),
            ],
        ),
        html.A(
            className="dashboard-hint",
            href="/prognose",
            children=[
                html.Span("arrow_forward", className="material-symbols-outlined"),
                "Detaillierte Stundenprognose und Personalempfehlungen öffnen",
            ],
        ),
    ])


def _kpi(label: str, value: str, icon: str, sub: str, variant: str) -> html.Div:
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(className="kpi-card__header", children=[
                html.Span(icon, className="material-symbols-outlined kpi-card__icon"),
                html.Span(label, className="kpi-card__label"),
            ]),
            html.Div(value, className="kpi-card__value"),
            html.Div(sub, className=f"kpi-card__sub kpi-card__sub--{variant}"),
        ],
    )


def render_app_layout() -> html.Div:
    return html.Div(
        className="app-shell",
        children=[
            dcc.Location(id="url", refresh=False),
            render_sidebar(),
            html.Div(
                className="main-wrapper",
                children=[
                    render_navbar(),
                    html.Main(
                        className="main-canvas",
                        id="page-content",
                        children=render_prognose_page(),
                    ),
                ],
            ),
        ],
    )