"""
layouts/staffing_actions.py
Personalempfehlungen – aus Prognosedaten abgeleitet, nicht hardcodiert.
"""

from __future__ import annotations
from dash import html


def _dot(severity: str) -> html.Div:
    cls = {
        "error":   "action-item__dot action-item__dot--error",
        "warning": "action-item__dot action-item__dot--secondary",
        "info":    "action-item__dot action-item__dot--neutral",
    }.get(severity, "action-item__dot action-item__dot--neutral")
    return html.Div(className=cls)


def _tag_cls(delta: str) -> str:
    if delta.startswith("+"):
        return "action-item__tag action-item__tag--add"
    if delta.startswith("-"):
        return "action-item__tag action-item__tag--remove"
    return "action-item__tag action-item__tag--add"


def render_action_item(
    title: str,
    description: str,
    delta: str,
    severity: str = "info",
    index: int = 0,
) -> html.Div:
    return html.Div(
        className="action-item",
        children=[
            html.Div(className="action-item__left", children=[
                _dot(severity),
                html.Div([
                    html.Div(title, className="action-item__title"),
                    html.Div(description, className="action-item__desc"),
                ]),
            ]),
            html.Div(
                className="action-item__right",
                children=[html.Span(delta, className=_tag_cls(delta))],
            ),
        ],
    )


def derive_actions_from_forecast(points: list[dict]) -> list[dict]:
    """
    Leitet Maßnahmen aus Prognosepunkten ab.

    Regeln:
      - Besucher > 80 und Staff < 4  → Unterbesetzungswarnung
      - Peak-Stunde                   → Verstärkungshinweis
      - Besucher < 20 und Staff > 2  → Überbesetzungsrisiko
    """
    if not points:
        return []

    actions: list[dict] = []
    peak = max(points, key=lambda p: p["predicted_visitors"])

    under = [
        p for p in points
        if p["predicted_visitors"] > 80 and p["recommended_staff"] < 4
    ]
    if under:
        start = under[0]["hour_label"]
        end   = under[-1]["hour_label"]
        gap   = 4 - under[0]["recommended_staff"]
        actions.append({
            "title":       f"Unterbesetzung: {start}–{end} Uhr",
            "description": "Hohe Besucherfrequenz, empfohlene Personalzahl unterschritten.",
            "delta":       f"+{gap} Mitarbeiter",
            "severity":    "error",
        })

    if peak["predicted_visitors"] > 50:
        actions.append({
            "title":       f"Spitzenzeit: {peak['hour_label']} Uhr",
            "description": f"Höchste Frequenz erwartet ({peak['predicted_visitors']} Besucher/h).",
            "delta":       f"{peak['recommended_staff']} Mitarbeiter empfohlen",
            "severity":    "warning",
        })

    over = [
        p for p in points
        if p["predicted_visitors"] < 20 and p["recommended_staff"] > 2
    ]
    if over:
        actions.append({
            "title":       f"Überbesetzungsrisiko: ab {over[0]['hour_label']} Uhr",
            "description": "Geringe Frequenz – Personalreduktion prüfen.",
            "delta":       "-1 Mitarbeiter",
            "severity":    "info",
        })

    return actions


def render_staffing_actions(actions: list[dict] | None = None) -> html.Div:
    items = actions or []
    count = len(items)
    rows = [
        render_action_item(
            title=a["title"],
            description=a["description"],
            delta=a["delta"],
            severity=a.get("severity", "info"),
            index=i,
        )
        for i, a in enumerate(items)
    ]
    return html.Div(
        className="actions-card",
        id="staffing-actions-container",
        children=[
            html.Div(
                className="actions-card__header",
                children=[
                    html.Div(
                        className="actions-card__header-title",
                        children=[
                            html.Span(
                                "engineering",
                                className="material-symbols-outlined",
                            ),
                            "Empfohlene Maßnahmen",
                        ],
                    ),
                    html.Span(
                        f"{count} Hinweis{'e' if count != 1 else ''}",
                        className="actions-card__badge",
                    ),
                ],
            ),
            html.Div(id="staffing-actions-list", children=rows),
        ],
    )