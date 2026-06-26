"""
callbacks/ui_callbacks.py
Tab-Routing: URL → Seiteninhalt + aktiver Nav-Link.
"""

from __future__ import annotations
import logging
from dash import Input, Output

logger = logging.getLogger(__name__)


def register_ui_callbacks(app) -> None:

    @app.callback(
        Output("page-content", "children"),
        Output("nav-home", "className"),
        Output("nav-prognose", "className"),
        Input("url", "pathname"),
    )
    def route(pathname: str):
        from layouts.dashboard import render_dashboard_page, render_prognose_page
        active   = "sidebar__nav-link sidebar__nav-link--active"
        inactive = "sidebar__nav-link"
        path = (pathname or "/").rstrip("/") or "/"
        logger.info("Route → %s", path)
        if path == "/prognose":
            return render_prognose_page(), inactive, active
        return render_dashboard_page(), active, inactive