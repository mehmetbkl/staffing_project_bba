"""
layouts/forecast_chart.py
Plotly-Diagramm: Besucher-Prognose (Balken) + empf. Personal (Linie).
Plotly 5+/6+ API: title=dict(text=..., font=dict(...))
"""

from __future__ import annotations
import logging
import plotly.graph_objects as go
from dash import dcc, html
from utils.constants import PLOT_COLORS

logger = logging.getLogger(__name__)


def build_forecast_figure(forecast_points: list[dict] | None = None) -> go.Figure:
    fig = go.Figure()

    if not forecast_points:
        fig.add_annotation(
            text="Noch keine Prognosedaten verfügbar",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False,
            font=dict(
                size=14,
                color=PLOT_COLORS["on_surface_var"],
                family="Inter, sans-serif",
            ),
        )
        fig.update_layout(**_base_layout())
        return fig

    hours    = [p["hour_label"] for p in forecast_points]
    visitors = [p["predicted_visitors"] for p in forecast_points]
    staff    = [p["recommended_staff"] for p in forecast_points]
    c_low    = [p.get("confidence_low") for p in forecast_points]
    c_high   = [p.get("confidence_high") for p in forecast_points]

    # Konfidenzband
    if any(v is not None for v in c_low):
        fig.add_trace(go.Scatter(
            x=hours + hours[::-1],
            y=c_high + c_low[::-1],
            fill="toself",
            fillcolor="rgba(17,92,185,0.08)",
            line=dict(color="rgba(0,0,0,0)"),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Balken: Nachfrage
    fig.add_trace(go.Bar(
        x=hours, y=visitors,
        name="Progn. Besucher",
        marker_color=PLOT_COLORS["surface_high"],
        marker_line_color=PLOT_COLORS["outline"],
        marker_line_width=1,
        opacity=0.85,
        hovertemplate="%{x}<br>%{y} Besucher<extra></extra>",
    ))

    # Linie: Personal (sekundäre Y-Achse)
    fig.add_trace(go.Scatter(
        x=hours, y=staff,
        name="Empf. Mitarbeiter",
        mode="lines+markers",
        line=dict(color=PLOT_COLORS["secondary"], width=3, shape="spline"),
        marker=dict(
            size=6,
            color=PLOT_COLORS["secondary"],
            line=dict(width=2, color="white"),
        ),
        yaxis="y2",
        hovertemplate="%{x}<br>%{y} Mitarbeiter<extra></extra>",
    ))

    layout = _base_layout()
    layout.update(
        yaxis=dict(
            title=dict(
                text="Besucher / Stunde",
                font=dict(size=11, color=PLOT_COLORS["on_surface_var"]),
            ),
            gridcolor=PLOT_COLORS["outline"],
            zeroline=False,
        ),
        yaxis2=dict(
            title=dict(
                text="Mitarbeiter",
                font=dict(size=11, color=PLOT_COLORS["secondary"]),
            ),
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=False,
            rangemode="tozero",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=11, family="Inter, sans-serif"),
        ),
        barmode="overlay",
    )
    fig.update_layout(**layout)
    return fig


def _base_layout() -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, sans-serif",
            color=PLOT_COLORS["on_surface"],
            size=12,
        ),
        margin=dict(l=8, r=8, t=8, b=8),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor=PLOT_COLORS["outline"],
            tickfont=dict(size=11),
        ),
        hovermode="x unified",
    )


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