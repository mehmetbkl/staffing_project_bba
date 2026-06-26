"""
layouts/dashboard.py
App-Shell mit dcc.Location-Routing.
/ → Dashboard-Seite    /prognose → Prognose-Seite
"""

from __future__ import annotations
from datetime import datetime
from dash import dcc, html

from layouts.forecast_chart import render_forecast_chart
from layouts.navbar import render_navbar
from layouts.sidebar import render_sidebar
from layouts.staffing_actions import derive_actions_from_forecast, render_staffing_actions
from layouts.summary_widget import render_summary_widget
from layouts.weather_widget import render_weather_widget
from services.forecast_service import get_placeholder_forecast
from services.shift_service import get_todays_shifts, get_shift_summary
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


# ── SCHICHTÜBERSICHT ─────────────────────────────────────────────────────────

_ROLE_AVATAR = {
    "Kassierer":        "shift-row__avatar shift-row__avatar--kassierer",
    "Abteilungsleiter": "shift-row__avatar shift-row__avatar--abteilungsleiter",
    "Lagerist":         "shift-row__avatar shift-row__avatar--lagerist",
}


def _status_pill(status: str) -> html.Span:
    labels = {
        "active":  ("Aktiv",      "shift-pill shift-pill--active"),
        "break":   ("Pause",      "shift-pill shift-pill--break"),
        "coming":  ("Kommt noch", "shift-pill shift-pill--coming"),
        "done":    ("Fertig",     "shift-pill shift-pill--done"),
    }
    text, cls = labels.get(status, ("–", "shift-pill"))
    return html.Span(text, className=cls)


def _shift_row(s: dict) -> html.Div:
    avatar_cls = _ROLE_AVATAR.get(s["role"], "shift-row__avatar shift-row__avatar--kassierer")
    return html.Div(className="shift-row", children=[
        html.Div(s["id"], className=avatar_cls),
        html.Div(className="shift-row__info", children=[
            html.Span(s["name"], className="shift-row__name"),
            html.Span(s["role"], className="shift-row__role"),
        ]),
        html.Span(f"{s['start']} – {s['end']}", className="shift-row__time"),
        _status_pill(s["status"]),
    ])


def _build_shift_content() -> list:
    """Baut den Inhalt der Schichtübersicht. Wird auch vom Callback genutzt."""
    shifts  = get_todays_shifts()
    summary = get_shift_summary()

    active_rows = [s for s in shifts if s["status"] in ("active", "break")]
    coming_rows = [s for s in shifts if s["status"] == "coming"]

    coverage_pct = summary["coverage_pct"]
    coverage_label = (
        f"{summary['active_now']} von {summary['total_today']} Mitarbeitern aktiv"
    )

    rows: list = []

    # Aktive Mitarbeiter
    for s in active_rows:
        rows.append(_shift_row(s))

    # Separator nur wenn es auch kommende gibt
    if coming_rows:
        rows.append(
            html.Div("Später heute", className="shift-overview__separator")
        )
        for s in coming_rows:
            rows.append(_shift_row(s))

    return [
        html.Div(className="shift-overview__header", children=[
            html.Div(className="shift-overview__title", children=[
                html.Span("badge", className="material-symbols-outlined"),
                "Aktuelle Schicht",
            ]),
            html.Div(className="shift-overview__header-right", children=[
                html.Span(
                    f"{summary['total_today']} Mitarbeiter heute",
                    className="shift-overview__meta",
                ),
                html.Span(
                    f"Stand: {datetime.now().strftime('%H:%M')} Uhr",
                    className="shift-overview__time",
                ),
            ]),
        ]),
        html.Div(className="shift-overview__coverage", children=[
            html.Div(className="shift-overview__coverage-label", children=[
                html.Span("Personaldeckung"),
                html.Span(
                    f"{coverage_label} · {coverage_pct} %",
                    className="shift-overview__coverage-value",
                ),
            ]),
            html.Div(className="shift-overview__coverage-track", children=[
                html.Div(
                    className="shift-overview__coverage-fill",
                    style={"width": f"{coverage_pct}%"},
                ),
            ]),
        ]),
        html.Div(className="shift-overview__list", children=rows),
    ]


def render_shift_overview() -> html.Div:
    """Schichtübersicht-Card mit id für Auto-Refresh via Callback."""
    return html.Div(
        id="shift-overview-container",
        className="shift-overview",
        children=_build_shift_content(),
    )


# ── SEITEN ───────────────────────────────────────────────────────────────────

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
        render_shift_overview(),
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
            # Auto-Refresh alle 60 Sekunden für die Schichtübersicht
            dcc.Interval(id="shift-interval", interval=60_000, n_intervals=0),
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