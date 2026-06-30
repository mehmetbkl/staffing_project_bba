"""
layouts/sidebar.py
Sidebar: nur Dashboard und Prognose.
"""

from __future__ import annotations
from dash import html
from utils.constants import NAV_ITEMS


def render_sidebar() -> html.Nav:
    return html.Nav(
        className="sidebar",
        children=[
            html.Div(
                className="sidebar__brand",
                children=[
                    html.Div(
                        className="sidebar__brand-icon",
                        children=html.Span(
                            "insights",
                            className="material-symbols-outlined",
                        ),
                    ),
                    html.Div([
                        html.Div("StaffCast", className="sidebar__brand-name"),
                        html.Div("Würzburg · Hubland", className="sidebar__brand-sub"),
                    ]),
                ],
            ),
            html.Div(
                className="sidebar__nav",
                children=[
                    html.A(
                        href=item["href"],
                        className="sidebar__nav-link",
                        id=f"nav-{item['href'].strip('/') or 'home'}",
                        children=[
                            html.Span(
                                item["icon"],
                                className="material-symbols-outlined",
                            ),
                            item["label"],
                        ],
                    )
                    for item in NAV_ITEMS
                ],
            ),
        ],
    )