"""
callbacks/ui_callbacks.py
Routing: URL → Seiteninhalt + aktiver Nav-Link (alle Tabs).
Info-Modal: öffnen/schließen über Topbar-Button, Close-Button und Backdrop.
Theme-Toggle: Hell-/Dunkelmodus (client-seitig via data-theme am <html>).
Auto-Refresh: Schichtübersicht jede Minute.
"""

from __future__ import annotations
import logging
from dash import Input, Output, State, ctx

from utils.constants import NAV_ITEMS

logger = logging.getLogger(__name__)

# Reihenfolge der Nav-Links = Reihenfolge der className-Outputs
_NAV_KEYS = [item["href"] for item in NAV_ITEMS]


def _nav_id(href: str) -> str:
    return f"nav-{href.strip('/') or 'home'}"


def register_ui_callbacks(app) -> None:

    # ── Routing ──────────────────────────────────────────────────────────────
    @app.callback(
        Output("page-content", "children"),
        [Output(_nav_id(h), "className") for h in _NAV_KEYS],
        Input("url", "pathname"),
        State("theme-store", "data"),
    )
    def route(pathname: str, theme: str | None):
        from layouts.dashboard import render_dashboard_page, render_prognose_page
        from layouts.history_page import render_history_page
        from layouts.personal_page import render_personal_page
        from layouts.model_page import render_model_page
        from layouts.coverage_page import render_coverage_page

        theme = theme if theme in ("light", "dark") else "light"
        active   = "sidebar__nav-link sidebar__nav-link--active"
        inactive = "sidebar__nav-link"
        path = (pathname or "/").rstrip("/") or "/"
        logger.info("Route → %s (theme=%s)", path, theme)

        # Seiten mit statischen Charts → Theme direkt mitgeben.
        pages = {
            "/":          render_dashboard_page,
            "/prognose":  render_prognose_page,
            "/deckung":   lambda: render_coverage_page(theme=theme),
            "/historie":  lambda: render_history_page(theme=theme),
            "/personal":  render_personal_page,
            "/modell":    render_model_page,
        }
        renderer = pages.get(path, render_dashboard_page)
        active_path = path if path in pages else "/"
        content = renderer()
        classes = [active if h == active_path else inactive for h in _NAV_KEYS]
        return content, *classes

    # ── Personalplan: Suche + Rollenfilter ───────────────────────────────────
    @app.callback(
        Output("plan-grid-container", "children"),
        Input("plan-search", "value"),
        Input("plan-role-filter", "value"),
        prevent_initial_call=True,
    )
    def filter_plan(search: str | None, role: str | None):
        from layouts.personal_page import build_plan_grid
        # build_plan_grid liefert den Container; hier nur dessen children.
        return build_plan_grid(search=search, role=role).children

    # ── Schichtübersicht Auto-Refresh ────────────────────────────────────────
    @app.callback(
        Output("shift-overview-container", "children"),
        Input("shift-interval", "n_intervals"),
    )
    def refresh_shift_overview(_):
        from layouts.dashboard import _build_shift_content
        return _build_shift_content()

    # ── Info-Modal öffnen / schließen ────────────────────────────────────────
    @app.callback(
        Output("info-modal", "className"),
        Input("info-button", "n_clicks"),
        Input("info-modal-close", "n_clicks"),
        Input("info-modal-backdrop", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_info_modal(_open, _close, _backdrop):
        if ctx.triggered_id == "info-button":
            return "info-modal"
        return "info-modal info-modal--hidden"
