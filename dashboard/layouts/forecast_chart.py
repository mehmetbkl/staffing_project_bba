"""
layouts/forecast_chart.py
Plotly-Diagramm: Besucher-Prognose (Balken) + empf. Personal (Linie).
Plotly 5+/6+ API: title=dict(text=..., font=dict(...))
"""

from __future__ import annotations
import logging
import plotly.graph_objects as go
from dash import dcc, html
from utils.chart_theme import base_layout, chart_palette

logger = logging.getLogger(__name__)


def build_forecast_figure(
    forecast_points: list[dict] | None = None,
    theme: str = "light",
) -> go.Figure:
    p = chart_palette(theme)
    fig = go.Figure()

    if not forecast_points:
        fig.add_annotation(
            text="Noch keine Prognosedaten verfügbar",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color=p["text_muted"], family="Inter, sans-serif"),
        )
        fig.update_layout(**base_layout(theme))
        return fig

    hours    = [pt["hour_label"] for pt in forecast_points]
    visitors = [pt["predicted_visitors"] for pt in forecast_points]
    staff    = [pt["recommended_staff"] for pt in forecast_points]
    c_low    = [pt.get("confidence_low") for pt in forecast_points]
    c_high   = [pt.get("confidence_high") for pt in forecast_points]

    # Konfidenzband
    if any(v is not None for v in c_low):
        fig.add_trace(go.Scatter(
            x=hours + hours[::-1],
            y=c_high + c_low[::-1],
            fill="toself",
            fillcolor=p["band"],
            line=dict(color="rgba(0,0,0,0)"),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Balken: Nachfrage
    fig.add_trace(go.Bar(
        x=hours, y=visitors,
        name="Progn. Besucher",
        marker_color=p["bar"],
        marker_line_color=p["bar_line"],
        marker_line_width=1,
        opacity=0.9,
        hovertemplate="%{x}<br>%{y} Besucher<extra></extra>",
    ))

    # Linie: Personal (sekundäre Y-Achse)
    fig.add_trace(go.Scatter(
        x=hours, y=staff,
        name="Empf. Mitarbeiter",
        mode="lines+markers",
        line=dict(color=p["accent"], width=3, shape="spline"),
        marker=dict(size=6, color=p["accent"],
                    line=dict(width=2, color=p["marker_border"])),
        yaxis="y2",
        hovertemplate="%{x}<br>%{y} Mitarbeiter<extra></extra>",
    ))

    layout = base_layout(theme)
    layout.update(
        yaxis=dict(
            title=dict(text="Besucher / Stunde",
                       font=dict(size=11, color=p["text_muted"])),
            gridcolor=p["grid"], zeroline=False, showline=False,
            tickfont=dict(size=11, color=p["text_muted"]),
        ),
        yaxis2=dict(
            title=dict(text="Mitarbeiter", font=dict(size=11, color=p["accent"])),
            overlaying="y", side="right", showgrid=False, zeroline=False,
            rangemode="tozero", tickfont=dict(size=11, color=p["text_muted"]),
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(size=11, family="Inter, sans-serif", color=p["text_muted"]),
        ),
        barmode="overlay",
    )
    fig.update_layout(**layout)
    return fig


def render_forecast_chart() -> html.Div:
    return html.Div(
        className="chart-card",
        children=[
            html.Div(
                className="chart-card__header",
                children=[
                    html.Div(
                        className="chart-card__title",
                        children=[
                            html.Span(
                                "monitoring",
                                className="material-symbols-outlined",
                            ),
                            "Nachfrage vs. Personalangebot",
                        ],
                    ),
                    html.Div(
                        className="chart-legend",
                        children=[
                            html.Div(className="chart-legend__item", children=[
                                html.Div(className="chart-legend__dot chart-legend__dot--supply"),
                                "Empf. Personal",
                            ]),
                            html.Div(className="chart-legend__item", children=[
                                html.Div(className="chart-legend__dot chart-legend__dot--demand"),
                                "Progn. Besucher",
                            ]),
                        ],
                    ),
                ],
            ),
            dcc.Graph(
                id="forecast-graph",
                figure=build_forecast_figure(None),
                config={"displayModeBar": False, "responsive": True},
                style={"height": "340px"},
            ),
        ],
    )