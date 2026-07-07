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
from utils.chart_theme import base_layout, chart_palette
from utils.formatting import format_date_de, format_visitors


def _trend_figure(theme: str = "light") -> go.Figure:
    p = chart_palette(theme)
    days = get_last_30_days()
    # Label als TT.MM. (deutsch) – als Kategorie behandeln, damit Plotly die
    # Strings nicht als Datum (mit falschem Jahr) interpretiert.
    x = [f"{d.iso_date[8:10]}.{d.iso_date[5:7]}." for d in days]
    y = [d.visitors for d in days]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines",
        line=dict(color=p["accent"], width=2.5, shape="spline"),
        fill="tozeroy", fillcolor=p["band"],
        hovertemplate="%{x}<br>%{y} Besucher<extra></extra>",
    ))
    layout = base_layout(theme)
    layout["xaxis"] = dict(
        type="category",
        showgrid=False, showline=True, linecolor=p["axis_line"],
        tickmode="array",
        tickvals=x[::5],          # nur jeden 5. Tag beschriften
        tickfont=dict(size=11, color=p["text_muted"]),
    )
    fig.update_layout(**layout)
    return fig


def _weekday_figure(theme: str = "light") -> go.Figure:
    p = chart_palette(theme)
    data = get_weekday_profile()
    fig = go.Figure(go.Bar(
        x=[d["weekday"] for d in data],
        y=[d["avg_visitors"] for d in data],
        marker_color=p["accent"],
        marker_line_width=0,
        hovertemplate="%{x}<br>%{y} Besucher (Ø)<extra></extra>",
    ))
    fig.update_layout(**base_layout(theme))
    return fig


def _hourly_figure(theme: str = "light") -> go.Figure:
    p = chart_palette(theme)
    data = get_hourly_profile()
    fig = go.Figure(go.Bar(
        x=[d["hour"] for d in data],
        y=[d["visitors"] for d in data],
        marker_color=p["accent_soft"],
        marker_line_color=p["accent"],
        marker_line_width=1,
        hovertemplate="%{x}<br>%{y} Besucher (Ø)<extra></extra>",
    ))
    fig.update_layout(**base_layout(theme))
    return fig


def _correlation_figure(theme: str = "light") -> go.Figure:
    p = chart_palette(theme)
    data = get_weather_correlation()
    fig = go.Figure(go.Scatter(
        x=[d["temp"] for d in data],
        y=[d["visitors"] for d in data],
        mode="markers",
        marker=dict(
            size=[6 + d["rain"] for d in data],
            color=[d["rain"] for d in data],
            colorscale=[[0, p["accent_soft"]], [1, p["accent"]]],
            showscale=True,
            colorbar=dict(title="Regen<br>mm", thickness=10, len=0.7,
                          tickfont=dict(color=p["text_muted"]),
                          title_font=dict(color=p["text_muted"])),
            line=dict(width=1, color=p["marker_border"]),
        ),
        hovertemplate="%{x} °C<br>%{y} Besucher<extra></extra>",
    ))
    layout = base_layout(theme)
    layout["hovermode"] = "closest"
    layout["xaxis"] = dict(
        title=dict(text="Ø Temperatur (°C)", font=dict(size=11, color=p["text_muted"])),
        showgrid=False, showline=True, linecolor=p["axis_line"],
        tickfont=dict(size=11, color=p["text_muted"]),
    )
    layout["yaxis"] = dict(
        title=dict(text="Besucher", font=dict(size=11, color=p["text_muted"])),
        gridcolor=p["grid"], zeroline=False,
        tickfont=dict(size=11, color=p["text_muted"]),
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


# Chart-IDs → Figur-Builder. Ermöglicht das Neu-Einfärben per Callback beim
# Theme-Wechsel (siehe callbacks/chart_callbacks.py). Reihenfolge = Anzeige.
HISTORY_FIGURES: dict[str, callable] = {
    "history-trend-graph":       _trend_figure,
    "history-weekday-graph":     _weekday_figure,
    "history-hourly-graph":      _hourly_figure,
    "history-correlation-graph": _correlation_figure,
}


def build_history_figures(theme: str = "light") -> list[go.Figure]:
    """Baut alle Historie-Figuren in der Reihenfolge von HISTORY_FIGURES.

    Wird vom Theme-Callback genutzt, um die bereits gerenderten Charts beim
    Umschalten hell/dunkel neu einzufärben – analog zum Prognose-Chart.
    """
    return [builder(theme) for builder in HISTORY_FIGURES.values()]


def _chart_panel(
    title: str, icon: str, fig: go.Figure, graph_id: str, height: int = 280
) -> html.Div:
    return html.Div(className="chart-card", children=[
        html.Div(className="chart-card__header", children=[
            html.Div(className="chart-card__title", children=[
                html.Span(icon, className="material-symbols-outlined"),
                title,
            ]),
        ]),
        dcc.Graph(
            id=graph_id,
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


def render_history_page(theme: str = "light") -> html.Div:
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

        _chart_panel("Besucherverlauf · 30 Tage", "show_chart",
                     _trend_figure(theme), "history-trend-graph", 300),

        html.Div(className="history-grid", children=[
            _chart_panel("Ø Besucher je Wochentag", "calendar_view_week",
                         _weekday_figure(theme), "history-weekday-graph"),
            _chart_panel("Typisches Tagesprofil", "schedule",
                         _hourly_figure(theme), "history-hourly-graph"),
        ]),

        _chart_panel(
            "Wetter-Korrelation · Temperatur vs. Besucher",
            "thermostat", _correlation_figure(theme), "history-correlation-graph", 320,
        ),
    ])
