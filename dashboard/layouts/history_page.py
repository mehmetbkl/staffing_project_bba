"""
layouts/history_page.py
Historie-/Trends-Seite: vergangene Besucherzahlen, Wochentag- und
Tagesprofil sowie Wetter-Korrelation. Daten aus history_service
(Platzhalter → später NeonDB).
"""

from __future__ import annotations
import plotly.graph_objects as go
from dash import dcc, html

from services.history_service import (
    get_history_summary, get_hourly_profile, get_last_30_days,
    get_weather_correlation, get_weekday_profile, is_live,
)
from utils.constants import PLOT_COLORS
from utils.formatting import format_date_de, format_visitors


def _chart_base() -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=PLOT_COLORS["on_surface"], size=12),
        margin=dict(l=8, r=8, t=8, b=8),
        hovermode="x unified",
        xaxis=dict(showgrid=False, showline=True, linecolor=PLOT_COLORS["outline"]),
        yaxis=dict(gridcolor=PLOT_COLORS["outline"], zeroline=False),
    )


def _trend_figure() -> go.Figure:
    days = get_last_30_days()
    # Label als TT.MM. (deutsch) – als Kategorie behandeln, damit Plotly die
    # Strings nicht als Datum (mit falschem Jahr) interpretiert.
    x = [f"{d.iso_date[8:10]}.{d.iso_date[5:7]}." for d in days]
    y = [d.visitors for d in days]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines",
        line=dict(color=PLOT_COLORS["secondary"], width=2.5, shape="spline"),
        fill="tozeroy", fillcolor="rgba(17,92,185,0.08)",
        hovertemplate="%{x}<br>%{y} Besucher<extra></extra>",
    ))
    layout = _chart_base()
    layout["xaxis"] = dict(
        type="category",
        showgrid=False, showline=True, linecolor=PLOT_COLORS["outline"],
        tickmode="array",
        tickvals=x[::5],          # nur jeden 5. Tag beschriften
        tickfont=dict(size=11),
    )
    fig.update_layout(**layout)
    return fig


def _weekday_figure() -> go.Figure:
    data = get_weekday_profile()
    fig = go.Figure(go.Bar(
        x=[d["weekday"] for d in data],
        y=[d["avg_visitors"] for d in data],
        marker_color=PLOT_COLORS["secondary"],
        marker_line_width=0,
        hovertemplate="%{x}<br>%{y} Besucher (Ø)<extra></extra>",
    ))
    fig.update_layout(**_chart_base())
    return fig


def _hourly_figure() -> go.Figure:
    data = get_hourly_profile()
    fig = go.Figure(go.Bar(
        x=[d["hour"] for d in data],
        y=[d["visitors"] for d in data],
        marker_color=PLOT_COLORS["secondary_light"],
        marker_line_color=PLOT_COLORS["secondary"],
        marker_line_width=1,
        hovertemplate="%{x}<br>%{y} Besucher (Ø)<extra></extra>",
    ))
    fig.update_layout(**_chart_base())
    return fig


def _correlation_figure() -> go.Figure:
    data = get_weather_correlation()
    fig = go.Figure(go.Scatter(
        x=[d["temp"] for d in data],
        y=[d["visitors"] for d in data],
        mode="markers",
        marker=dict(
            size=[6 + d["rain"] for d in data],
            color=[d["rain"] for d in data],
            colorscale=[[0, PLOT_COLORS["secondary_light"]], [1, PLOT_COLORS["secondary"]]],
            showscale=True,
            colorbar=dict(title="Regen<br>mm", thickness=10, len=0.7),
            line=dict(width=1, color="white"),
        ),
        hovertemplate="%{x} °C<br>%{y} Besucher<extra></extra>",
    ))
    layout = _chart_base()
    layout["hovermode"] = "closest"
    layout["xaxis"] = dict(
        title=dict(text="Ø Temperatur (°C)", font=dict(size=11)),
        showgrid=False, showline=True, linecolor=PLOT_COLORS["outline"],
    )
    layout["yaxis"] = dict(
        title=dict(text="Besucher", font=dict(size=11)),
        gridcolor=PLOT_COLORS["outline"], zeroline=False,
    )
    fig.update_layout(**layout)
    return fig


def _kpi(label: str, value: str, sub: str, icon: str) -> html.Div:
    return html.Div(className="kpi-card", children=[
        html.Div(className="kpi-card__header", children=[
            html.Span(icon, className="material-symbols-outlined kpi-card__icon"),
            html.Span(label, className="kpi-card__label"),
        ]),
        html.Div(value, className="kpi-card__value"),
        html.Div(sub, className="kpi-card__sub kpi-card__sub--neutral"),
    ])


def _chart_panel(title: str, icon: str, fig: go.Figure, height: int = 280) -> html.Div:
    return html.Div(className="chart-card", children=[
        html.Div(className="chart-card__header", children=[
            html.Div(className="chart-card__title", children=[
                html.Span(icon, className="material-symbols-outlined"),
                title,
            ]),
        ]),
        dcc.Graph(
            figure=fig,
            config={"displayModeBar": False, "responsive": True},
            style={"height": f"{height}px"},
        ),
    ])


def _status_banner() -> html.Div:
    """Zeigt je nach Datenlage einen Live- oder Demo-Hinweis."""
    if is_live():
        return html.Div(className="status-banner status-banner--live", children=[
            html.Span("database", className="material-symbols-outlined"),
            "Live-Daten aus der NeonDB (raw.library_visitors · raw.weather).",
        ])
    return html.Div(className="demo-banner", children=[
        html.Span("science", className="material-symbols-outlined"),
        "Demodaten – DB nicht erreichbar oder leer. Sobald Daten in der NeonDB liegen, "
        "wird diese Auswertung automatisch live.",
    ])


def render_history_page() -> html.Div:
    s = get_history_summary()
    return html.Div([
        html.Div(className="page-header", children=[html.Div([
            html.H2("Historie & Trends", className="page-header__title"),
            html.P(
                format_date_de() + " · Hubland, Würzburg · letzte 30 Tage",
                className="page-header__subtitle",
            ),
        ])]),

        _status_banner(),

        html.Div(className="dashboard-kpi-grid", children=[
            _kpi("Ø Besucher / Tag", format_visitors(s["avg_per_day"]),
                 "Mittel über 30 Tage", "groups"),
            _kpi("Summe 30 Tage", format_visitors(s["total_30d"]),
                 "Gesamtbesucher", "functions"),
            _kpi("Stärkster Tag", format_visitors(s["busiest_value"]),
                 s["busiest_date"], "trending_up"),
            _kpi("Ruhigster Tag", format_visitors(s["quietest_value"]),
                 s["quietest_date"], "trending_down"),
        ]),

        _chart_panel("Besucherverlauf · 30 Tage", "show_chart", _trend_figure(), 300),

        html.Div(className="history-grid", children=[
            _chart_panel("Ø Besucher je Wochentag", "calendar_view_week", _weekday_figure()),
            _chart_panel("Typisches Tagesprofil", "schedule", _hourly_figure()),
        ]),

        _chart_panel(
            "Wetter-Korrelation · Temperatur vs. Besucher",
            "thermostat", _correlation_figure(), 320,
        ),
    ])
