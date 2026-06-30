"""
layouts/navbar.py
Topbar – App-Titel, Theme-Umschalter und globaler Info-Button.
"""

from __future__ import annotations
from dash import html


def render_navbar() -> html.Header:
    return html.Header(
        className="topbar",
        children=[
            html.Div("StaffCast", className="topbar__title"),
            html.Div(
                className="topbar__actions",
                children=[
                    html.Button(
                        id="theme-toggle",
                        className="topbar__icon-btn",
                        title="Hell-/Dunkelmodus umschalten",
                        n_clicks=0,
                        children=html.Span(
                            "dark_mode",
                            id="theme-toggle-icon",
                            className="material-symbols-outlined",
                        ),
                    ),
                    html.Button(
                        id="info-button",
                        className="topbar__icon-btn topbar__icon-btn--accent",
                        title="Worauf basiert die Prognose?",
                        n_clicks=0,
                        children=[
                            html.Span("info", className="material-symbols-outlined"),
                            html.Span("Info", className="topbar__icon-btn-label"),
                        ],
                    ),
                ],
            ),
        ],
    )
