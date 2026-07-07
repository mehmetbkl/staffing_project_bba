"""
utils/chart_theme.py
Zentrale Farb-/Layout-Paletten für Plotly-Charts – getrennt nach hell/dunkel.

So sehen die Diagramme in beiden Themes nativ aus (echte dunkle Charts im
Dark-Mode statt einer hellen Box). build_*_figure() nehmen ein `theme`-Argument
und ein clientseitiger Callback (siehe app.py) färbt die bereits gerenderten
Charts beim Theme-Wechsel um, ohne den Server zu fragen.
"""

from __future__ import annotations

# Markenfarben (themeunabhängig)
ACCENT = "#3b82f6"          # Linie „Empf. Personal"
ACCENT_SOFT = "#93b8f5"
BAND = "rgba(59,130,246,0.10)"   # Konfidenzband


def chart_palette(theme: str = "light") -> dict:
    """Liefert die Farb-/Achsenwerte für das gewünschte Theme."""
    if theme == "dark":
        return {
            "paper": "rgba(0,0,0,0)",
            "plot": "rgba(0,0,0,0)",
            "text": "#c8cdd6",
            "text_muted": "#9aa0aa",
            "grid": "#283039",
            "axis_line": "#39414d",
            "bar": "#2d3742",
            "bar_line": "#3d4856",
            "accent": ACCENT,
            "accent_soft": ACCENT_SOFT,
            "band": "rgba(59,130,246,0.14)",
            "marker_border": "#161b23",
        }
    return {
        "paper": "rgba(0,0,0,0)",
        "plot": "rgba(0,0,0,0)",
        "text": "#191c1d",
        "text_muted": "#5b6470",
        "grid": "#e6e8ec",
        "axis_line": "#c9cdd6",
        "bar": "#e3e6ea",
        "bar_line": "#c4c6cf",
        "accent": "#115cb9",
        "accent_soft": ACCENT_SOFT,
        "band": "rgba(17,92,185,0.08)",
        "marker_border": "#ffffff",
    }


def base_layout(theme: str = "light") -> dict:
    """Gemeinsame, dezente Layout-Basis für alle Charts."""
    p = chart_palette(theme)
    return dict(
        paper_bgcolor=p["paper"],
        plot_bgcolor=p["plot"],
        font=dict(family="Inter, sans-serif", color=p["text"], size=12),
        margin=dict(l=8, r=8, t=8, b=8),
        xaxis=dict(
            showgrid=False, showline=True, linecolor=p["axis_line"],
            tickfont=dict(size=11, color=p["text_muted"]), ticks="outside",
            ticklen=4, tickcolor=p["axis_line"],
        ),
        yaxis=dict(
            gridcolor=p["grid"], zeroline=False, showline=False,
            tickfont=dict(size=11, color=p["text_muted"]),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1a2029" if theme == "dark" else "#ffffff",
            bordercolor=p["axis_line"],
            font=dict(family="Inter, sans-serif", size=12, color=p["text"]),
        ),
    )
