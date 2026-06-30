"""
layouts/personal_page.py
Personalplanung: Wochen-Schichtplan aller Mitarbeiter aus employees.py.
"""

from __future__ import annotations
from dash import html

from services.shift_service import (
    WEEKDAY_LABELS_DE, WEEKDAY_ORDER,
    get_team_summary, get_weekly_coverage, get_weekly_plan,
)
from utils.formatting import format_date_de


_ROLE_AVATAR = {
    "Kassierer":        "shift-row__avatar--kassierer",
    "Abteilungsleiter": "shift-row__avatar--abteilungsleiter",
    "Lagerist":         "shift-row__avatar--lagerist",
}


def _kpi(label: str, value: str, sub: str, icon: str) -> html.Div:
    return html.Div(className="kpi-card", children=[
        html.Div(className="kpi-card__header", children=[
            html.Span(icon, className="material-symbols-outlined kpi-card__icon"),
            html.Span(label, className="kpi-card__label"),
        ]),
        html.Div(value, className="kpi-card__value"),
        html.Div(sub, className="kpi-card__sub kpi-card__sub--neutral"),
    ])


def _today_index() -> int:
    import datetime as _dt
    return _dt.datetime.now().weekday()  # 0 = Mon


def _plan_header() -> html.Div:
    today = _today_index()
    cells = [html.Div("Mitarbeiter", className="plan-grid__corner")]
    for i, wd in enumerate(WEEKDAY_ORDER):
        cls = "plan-grid__dayhead"
        if i == today:
            cls += " plan-grid__dayhead--today"
        cells.append(html.Div(WEEKDAY_LABELS_DE[wd], className=cls))
    cells.append(html.Div("Std.", className="plan-grid__hourhead"))
    return html.Div(className="plan-grid__row plan-grid__row--head", children=cells)


def _plan_row(p: dict) -> html.Div:
    today = _today_index()
    avatar_cls = "shift-row__avatar " + _ROLE_AVATAR.get(
        p["role"], "shift-row__avatar--kassierer"
    )
    cells = [
        html.Div(className="plan-grid__person", children=[
            html.Div(p["id"], className=avatar_cls),
            html.Div(className="plan-grid__person-info", children=[
                html.Span(p["name"], className="plan-grid__person-name"),
                html.Span(p["role"], className="plan-grid__person-role"),
            ]),
        ]),
    ]
    for i, wd in enumerate(WEEKDAY_ORDER):
        val = p["days"][wd]
        cell_cls = "plan-grid__cell"
        if i == today:
            cell_cls += " plan-grid__cell--today"
        if val:
            cells.append(html.Div(
                className=cell_cls + " plan-grid__cell--shift",
                children=html.Span(val, className="plan-grid__shift"),
            ))
        else:
            cells.append(html.Div("–", className=cell_cls + " plan-grid__cell--off"))
    cells.append(html.Div(f"{p['total_hours']:.0f} h", className="plan-grid__hours"))
    return html.Div(className="plan-grid__row", children=cells)


def _coverage_bar() -> html.Div:
    cov = get_weekly_coverage()
    today = _today_index()
    max_count = max((c["count"] for c in cov), default=1) or 1
    bars = []
    for i, c in enumerate(cov):
        h = int(c["count"] / max_count * 100)
        bar_cls = "coverage-bar__fill"
        if i == today:
            bar_cls += " coverage-bar__fill--today"
        bars.append(html.Div(className="coverage-bar__col", children=[
            html.Div(str(c["count"]), className="coverage-bar__count"),
            html.Div(className="coverage-bar__track", children=[
                html.Div(className=bar_cls, style={"height": f"{h}%"}),
            ]),
            html.Div(c["label"], className="coverage-bar__label"),
        ]))
    return html.Div(className="card", children=[
        html.Div(className="card__header", children=[
            html.Span("bar_chart", className="material-symbols-outlined card__header-icon"),
            "Besetzung je Wochentag",
        ]),
        html.Div(className="coverage-bar", children=bars),
    ])


def _source_banner() -> html.Div:
    """Zeigt, ob die Personaldaten live aus der DB (staff-Schema) kommen."""
    from data.employees import employees_source
    if employees_source() == "db":
        return html.Div(className="status-banner status-banner--live", children=[
            html.Span("database", className="material-symbols-outlined"),
            "Live-Schichtplan aus der NeonDB (staff.employees · staff.shifts) – "
            "heute ist hervorgehoben.",
        ])
    return html.Div(className="demo-banner", children=[
        html.Span("badge", className="material-symbols-outlined"),
        "Schichtplan aus dem Fallback (data/employees.py) – DB nicht erreichbar. "
        "Heute ist hervorgehoben.",
    ])


def render_personal_page() -> html.Div:
    plan = get_weekly_plan()
    s = get_team_summary()
    roles_str = " · ".join(f"{n}× {r}" for r, n in s["roles"].items())

    return html.Div([
        html.Div(className="page-header", children=[html.Div([
            html.H2("Personalplanung", className="page-header__title"),
            html.P(
                format_date_de() + " · Wochenübersicht aller Mitarbeiter",
                className="page-header__subtitle",
            ),
        ])]),

        _source_banner(),

        html.Div(className="dashboard-kpi-grid", children=[
            _kpi("Mitarbeiter", str(s["headcount"]), roles_str, "groups"),
            _kpi("Personalstunden / Woche", f"{s['total_hours']:.0f} h",
                 "Summe aller Schichten", "schedule"),
            _kpi("Stärkster Tag", s["busiest_day"],
                 f"{s['busiest_count']} Mitarbeiter eingeplant", "trending_up"),
            _kpi("Ø Stunden / MA", f"{s['total_hours'] / max(s['headcount'], 1):.0f} h",
                 "pro Woche", "person"),
        ]),

        html.Div(className="plan-card", children=[
            html.Div(className="plan-card__header", children=[
                html.Div(className="plan-card__title", children=[
                    html.Span("calendar_month", className="material-symbols-outlined"),
                    "Wochen-Schichtplan",
                ]),
            ]),
            html.Div(className="plan-grid", children=[
                _plan_header(),
                *[_plan_row(p) for p in plan],
            ]),
        ]),

        _coverage_bar(),
    ])
