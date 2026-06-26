"""
layouts/navbar.py
Topbar – nur App-Titel.
"""

from __future__ import annotations
from dash import html


def render_navbar() -> html.Header:
    return html.Header(
        className="topbar",
        children=[
            html.Div("StaffCast", className="topbar__title"),
        ],
    )