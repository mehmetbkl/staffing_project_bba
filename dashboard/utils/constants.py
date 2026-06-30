"""
utils/constants.py
Globale Konstanten.
"""

LIBRARY_LAT: float = 49.7913
LIBRARY_LON: float = 9.9534
LOCATION_LABEL: str = "Würzburg · Hubland"

WEATHER_START_DATE: str = "2025-04-24"
WEATHER_BASE_URL: str = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"
WEATHER_TIMEZONE: str = "Europe/Berlin"

WMO_CODE_MAP: dict[int, tuple[str, str]] = {
    0:  ("clear_day",         "Klar"),
    1:  ("partly_cloudy_day", "Überwiegend klar"),
    2:  ("partly_cloudy_day", "Teilweise bewölkt"),
    3:  ("cloud",             "Bedeckt"),
    45: ("foggy",             "Nebel"),
    48: ("foggy",             "Gefrierender Nebel"),
    51: ("rainy_light",       "Leichter Nieselregen"),
    53: ("rainy",             "Nieselregen"),
    55: ("rainy_heavy",       "Starker Nieselregen"),
    61: ("rainy_light",       "Leichter Regen"),
    63: ("rainy",             "Regen"),
    65: ("rainy_heavy",       "Starker Regen"),
    71: ("weather_snowy",     "Leichter Schneefall"),
    73: ("weather_snowy",     "Schneefall"),
    75: ("weather_snowy",     "Starker Schneefall"),
    80: ("rainy_light",       "Leichte Schauer"),
    81: ("rainy",             "Schauer"),
    82: ("rainy_heavy",       "Starke Schauer"),
    85: ("weather_snowy",     "Schneeschauer"),
    95: ("thunderstorm",      "Gewitter"),
    96: ("thunderstorm",      "Gewitter mit Hagel"),
    99: ("thunderstorm",      "Starkes Gewitter mit Hagel"),
}

DEFAULT_WEATHER_ICON: str = "cloud"
DEFAULT_WEATHER_DESC: str = "Unbekannt"

WEATHER_REFRESH_INTERVAL_MS: int = 15 * 60 * 1000

PLOT_COLORS = {
    "primary":        "#000a1e",
    "secondary":      "#115cb9",
    "secondary_light":"#acc7ff",
    "surface":        "#edeeef",
    "surface_high":   "#e1e3e4",
    "outline":        "#c4c6cf",
    "on_surface":     "#191c1d",
    "on_surface_var": "#44474e",
    "error":          "#ba1a1a",
    "background":     "#f8f9fa",
}

STAFFING_THRESHOLDS: list[tuple[int, int]] = [
    (0,   1),
    (20,  2),
    (50,  3),
    (80,  4),
    (120, 5),
    (160, 6),
    (200, 7),
]

NAV_ITEMS: list[dict] = [
    {"label": "Dashboard",       "icon": "dashboard",      "href": "/"},
    {"label": "Prognose",        "icon": "query_stats",    "href": "/prognose"},
    {"label": "Historie",        "icon": "show_chart",     "href": "/historie"},
    {"label": "Personalplanung", "icon": "calendar_month", "href": "/personal"},
    {"label": "Modell-Insights", "icon": "analytics",      "href": "/modell"},
]