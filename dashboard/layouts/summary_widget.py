"""
layouts/summary_widget.py
Tagesübersicht (Dark Card) – Werte aus Prognose.
"""

from __future__ import annotations
from dash import html
from utils.formatting import format_hours, format_visitors


def render_summary_widget(
    predicted_traffic: int | None = None,
    recommended_hours: float | None = None,
    traffic_change_pct: float | None = None,
) -> html.Div:
    badge = None
    if traffic_change_pct is not None:
        sign = "+" if traffic_change_pct >= 0 else ""
        cls = (
            "summary-item__badge summary-item__badge--positive"
            if traffic_change_pct >= 0
            else "summary-item__badge summary-item__badge--negative"
        )
        badge = html.Span(f"{sign}{traffic_change_pct:.0f} %", className=cls)

    traffic_children = [format_visitors(predicted_traffic)]
    if badge:
        traffic_children.append(badge)

    return html.Div(
        className="card card--dark",
        children=[
            html.Div(
                className="card__header",
                children=[
                    html.Span(
                        "insights",
                        className="material-symbols-outlined card__header-icon",
                    ),
                    "Tagesübersicht",
                ],
            ),
            html.Div(
                className="summary-grid",
                children=[
                    html.Div([
                        html.Div("Progn. Besucher", className="summary-item__label"),
                        html.Div(traffic_children, className="summary-item__value"),
                    ]),
                    html.Div([
                        html.Div("Empf. Stunden", className="summary-item__label"),
                        html.Div(
                            format_hours(recommended_hours),
                            className="summary-item__value",
                        ),
                    ]),
                ],
            ),
        ],
    )