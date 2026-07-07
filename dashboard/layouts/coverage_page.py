"""
layouts/coverage_page.py
Bedarf vs. Besetzung: Vergleicht den stündlichen Personalbedarf (Prognose) mit
der eingeplanten Besetzung (Schichtplan) und zeigt Über-/Unterdeckung je Stunde.
"""

from __future__ import annotations
import plotly.graph_objects as go
from dash import dcc, html

from services.coverage_service import get_coverage_today, get_coverage_summary
from utils.chart_theme import base_layout, chart_palette
from utils.formatting import format_date_de


def build_coverage_figure(theme: str = "light") -> go.Figure:
    """Balken: eingeplante Besetzung; Linie: benötigter Bedarf je Stunde."""
    p = chart_palette(theme)
    rows = get_coverage_today()
    x = [r["hour_label"] for r in rows]
    scheduled = [r["scheduled"] for r in rows]
    required = [r["required"] for r in rows]

    # Balkenfarbe je Deckungsstatus: Unterdeckung rot, sonst neutral/grün.
    bar_colors = [
        "#ef4444" if r["status"] == "under" else p["accent_soft"]
        for r in rows
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x, y=scheduled, name="Eingeplant",
        marker_color=bar_colors, marker_line_width=0,
        hovertemplate="%{x}<br>%{y} eingeplant<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x, y=required, name="Bedarf (Prognose)",
        mode="lines+markers",
        line=dict(color=p["accent"], width=2.5, shape="spline"),
        marker=dict(size=6, color=p["accent"]),
        hovertemplate="%{x}<br>%{y} benötigt<extra></extra>",
    ))

    layout = base_layout(theme)
    layout["barmode"] = "overlay"
    layout["showlegend"] = True
    layout["legend"] = dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(size=11, color=p["text_muted"]),
    )
    layout["xaxis"] = dict(
        type="category", showgrid=False, showline=True, linecolor=p["axis_line"],
        tickfont=dict(size=11, color=p["text_muted"]),
    )
    layout["yaxis"] = dict(
        gridcolor=p["grid"], zeroline=False, dtick=1,
        tickfont=dict(size=11, color=p["text_muted"]),
    )
    fig.update_layout(**layout)
    return fig


def _kpi(label: str, value: str, sub: str, icon: str, variant: str = "neutral") -> html.Div:
    return html.Div(className="kpi-card", children=[
        html.Div(className="kpi-card__header", children=[
            html.Span(icon, className="material-symbols-outlined kpi-card__icon"),
            html.Span(label, className="kpi-card__label"),
        ]),
        html.Div(value, className="kpi-card__value"),
        html.Div(sub, className=f"kpi-card__sub kpi-card__sub--{variant}"),
    ])


def _gap_pill(status: str, gap: int) -> html.Span:
    if status == "under":
        return html.Span(f"{gap} MA fehlt" if gap == -1 else f"{gap} MA fehlen",
                         className="gap-pill gap-pill--under")
    if status == "over":
        return html.Span(f"+{gap} MA", className="gap-pill gap-pill--over")
    return html.Span("gedeckt", className="gap-pill gap-pill--ok")


def _gap_row(r: dict) -> html.Div:
    return html.Div(className="gap-row", children=[
        html.Span(r["hour_label"], className="gap-row__hour"),
        html.Div(className="gap-row__bars", children=[
            html.Span(f"Bedarf {r['required']}", className="gap-row__req"),
            html.Span("→", className="gap-row__arrow"),
            html.Span(f"Eingeplant {r['scheduled']}", className="gap-row__sched"),
        ]),
        _gap_pill(r["status"], r["gap"]),
    ])


def _gap_table() -> html.Div:
    rows = get_coverage_today()
    # Nur relevante Stunden zeigen: erst Unterdeckung, dann Rest chronologisch.
    under = [r for r in rows if r["status"] == "under"]
    rest = [r for r in rows if r["status"] != "under"]
    ordered = under + rest

    if not rows:
        body = [html.Div("Keine Prognosedaten verfügbar.", className="gap-row__empty")]
    else:
        body = [_gap_row(r) for r in ordered]

    return html.Div(className="card", children=[
        html.Div(className="card__header", children=[
            html.Span("checklist", className="material-symbols-outlined card__header-icon"),
            "Deckung je Stunde – Unterdeckung zuerst",
        ]),
        html.Div(className="gap-list", children=body),
    ])


def render_coverage_page(theme: str = "light") -> html.Div:
    s = get_coverage_summary()

    cov_variant = "warning" if s["under_hours"] > 0 else "positive"
    return html.Div([
        html.Div(className="page-header", children=[html.Div([
            html.H2("Bedarf vs. Besetzung", className="page-header__title"),
            html.P(
                format_date_de() + " · Prognose-Bedarf gegen heutigen Schichtplan",
                className="page-header__subtitle",
            ),
        ])]),

        html.Div(className="dashboard-kpi-grid", children=[
            _kpi("Deckungsgrad", f"{s['coverage_pct']} %",
                 f"{s['ok_hours'] + s['over_hours']} von "
                 f"{s['ok_hours'] + s['over_hours'] + s['under_hours']} Std. gedeckt",
                 "verified", "positive" if s["coverage_pct"] >= 80 else "warning"),
            _kpi("Unterdeckte Stunden", str(s["under_hours"]),
                 "Bedarf > eingeplant", "error",
                 "error" if s["under_hours"] > 0 else "neutral"),
            _kpi("Größte Lücke", s["peak_gap_hour"],
                 f"{s['peak_gap']} MA fehlen" if s["peak_gap"] else "keine Lücke",
                 "priority_high", "error" if s["peak_gap"] else "positive"),
            _kpi("Personalstunden", f"{s['total_scheduled']} / {s['total_required']}",
                 "eingeplant / benötigt", "schedule",
                 "warning" if s["total_scheduled"] < s["total_required"] else "positive"),
        ]),

        html.Div(className="chart-card", children=[
            html.Div(className="chart-card__header", children=[
                html.Div(className="chart-card__title", children=[
                    html.Span("bar_chart", className="material-symbols-outlined"),
                    "Bedarf (Linie) vs. eingeplante Besetzung (Balken)",
                ]),
            ]),
            dcc.Graph(
                id="coverage-graph",
                figure=build_coverage_figure(theme),
                config={"displayModeBar": False, "responsive": True},
                style={"height": "320px"},
            ),
        ]),

        _gap_table(),
    ])
