"""
layouts/model_page.py
Modell-Insights: erklärt Datenfluss, Features, Methodik und Status der
Besucher-Prognose. Statischer Erklär-Tab (keine Live-Daten nötig).
"""

from __future__ import annotations
from dash import html

from services.db import db_available
from services.forecast_service import get_forecast, forecast_source
from services.history_service import get_last_30_days, is_live as history_live


_FEATURES = [
    ("calendar_month", "Wochentag", "Mo–So als saisonales Merkmal – Wochenenden weichen stark ab."),
    ("schedule", "Tageszeit", "Stunde des Tages; bildet die typische Vormittags-/Nachmittagskurve ab."),
    ("event", "Feiertage & Ferien", "Feiertags- und Ferienindikatoren aus dem holidays-Datensatz."),
    ("thermostat", "Temperatur", "Open-Meteo-Wert; beeinflusst, ob Besucher kommen oder draußen bleiben."),
    ("rainy", "Niederschlag", "Regen erhöht tendenziell die Besucherzahl in der Bibliothek."),
    ("cloud", "Bewölkung & Wind", "Sekundäre Wetterfaktoren mit geringerem, aber messbarem Einfluss."),
]

_PIPELINE = [
    ("database", "Rohdaten", "Historische Besucherzahlen (NeonDB) + Wetterarchiv (Open-Meteo)."),
    ("cleaning_services", "Aufbereitung", "Zusammenführen, Lücken füllen, Merkmale erzeugen → gold.feature_store (ETL)."),
    ("query_stats", "Prognosemodell", "futureEXPERT bzw. saisonale Baseline schätzen die Besucher je Tag."),
    ("rule", "Personalregel", "Schwellenwerte übersetzen Besucher → empfohlene Mitarbeiter."),
    ("insights", "Dashboard", "Prognose, Konfidenzband und Maßnahmen werden angezeigt."),
]


def _feature_card(icon: str, title: str, desc: str) -> html.Div:
    return html.Div(className="feature-card", children=[
        html.Span(icon, className="material-symbols-outlined feature-card__icon"),
        html.Div([
            html.Div(title, className="feature-card__title"),
            html.Div(desc, className="feature-card__desc"),
        ]),
    ])


def _pipeline_step(i: int, icon: str, title: str, desc: str, last: bool) -> html.Div:
    children = [
        html.Div(className="pipeline__node", children=[
            html.Span(icon, className="material-symbols-outlined"),
        ]),
        html.Div(className="pipeline__body", children=[
            html.Div(f"{i}. {title}", className="pipeline__title"),
            html.Div(desc, className="pipeline__desc"),
        ]),
    ]
    cls = "pipeline__step" + ("" if last else " pipeline__step--connected")
    return html.Div(className=cls, children=children)


def _status_row(label: str, state: str) -> html.Div:
    is_live = state == "live"
    badge_cls = "model-status__badge model-status__badge--" + ("live" if is_live else "pending")
    badge_txt = "Live angebunden" if is_live else "In Integration"
    return html.Div(className="model-status__row", children=[
        html.Span(
            "check_circle" if is_live else "pending",
            className="material-symbols-outlined model-status__icon "
                     + ("model-status__icon--live" if is_live else "model-status__icon--pending"),
        ),
        html.Span(label, className="model-status__label"),
        html.Span(badge_txt, className=badge_cls),
    ])


def _status_rows() -> list:
    """Baut die Statuszeilen anhand der echten Datenlage."""
    get_last_30_days()          # setzt das Live-Flag der Historie
    forecast = get_forecast()   # setzt die Prognose-Quelle
    hist = history_live()
    src = forecast_source()     # 'db' | 'csv' | 'demo'
    pred_live = src in ("db", "csv")

    return [
        _status_row("Wetterdaten (Open-Meteo)", "live"),
        _status_row("Historische Besucherzahlen (DB)", "live" if hist else "pending"),
        _status_row("Besucher-Prognose (Modell)", "live" if pred_live else "pending"),
        _status_row("Personalempfehlung (Regel)", "live"),
    ]


def _status_note() -> str:
    forecast = get_forecast()
    src = forecast_source()
    if src == "db":
        return ("Die Besucher-Prognose kommt live aus gold.predictions. "
                "Das Stundenprofil wird aus der Tagesprognose abgeleitet.")
    if src == "csv":
        return ("Die Besucher-Prognose stammt aus der Modell-CSV (forecast_besucher.csv, "
                "DB-Tabelle gold.predictions noch leer). Das Stundenprofil wird "
                "aus der Tagesprognose abgeleitet.")
    return ("Aktuell läuft die Besucher-Prognose über ein festes Demo-Profil "
            "(weder gold.predictions noch die CSV verfügbar). Sobald das Modell "
            "Ergebnisse liefert, fließen sie automatisch ein – das Interface bleibt gleich.")


def render_model_page() -> html.Div:
    return html.Div([
        html.Div(className="page-header", children=[html.Div([
            html.H2("Modell-Insights", className="page-header__title"),
            html.P(
                "So entsteht die Nachfrageprognose von StaffCast",
                className="page-header__subtitle",
            ),
        ])]),

        html.Div(className="card card--dark model-intro", children=[
            html.Div(className="model-intro__icon", children=[
                html.Span("query_stats", className="material-symbols-outlined"),
            ]),
            html.Div([
                html.Div("Ziel der Prognose", className="model-intro__label"),
                html.P(
                    "StaffCast schätzt, wie viele Besucher die Bibliothek je Stunde "
                    "erwartet, und leitet daraus eine Personalempfehlung ab. So lassen "
                    "sich Über- und Unterbesetzung erkennen, bevor sie entstehen.",
                    className="model-intro__text",
                ),
            ]),
        ]),

        html.Div(className="card", children=[
            html.Div(className="card__header", children=[
                html.Span("conversion_path", className="material-symbols-outlined card__header-icon"),
                "Datenfluss",
            ]),
            html.Div(className="pipeline", children=[
                _pipeline_step(i + 1, ic, t, d, last=(i == len(_PIPELINE) - 1))
                for i, (ic, t, d) in enumerate(_PIPELINE)
            ]),
        ]),

        html.Div(className="card", children=[
            html.Div(className="card__header", children=[
                html.Span("tune", className="material-symbols-outlined card__header-icon"),
                "Einflussfaktoren (Features)",
            ]),
            html.Div(className="feature-grid", children=[
                _feature_card(ic, t, d) for ic, t, d in _FEATURES
            ]),
        ]),

        html.Div(className="model-two-col", children=[
            html.Div(className="card", children=[
                html.Div(className="card__header", children=[
                    html.Span("rule", className="material-symbols-outlined card__header-icon"),
                    "Von Besuchern zu Personal",
                ]),
                html.P(
                    "Aus der geschätzten Besucherzahl pro Stunde wird über feste "
                    "Schwellenwerte die empfohlene Mitarbeiterzahl bestimmt:",
                    className="model-rule__lead",
                ),
                html.Div(className="info-thresholds", children=[
                    html.Div(className="info-threshold", children=[
                        html.Span(f"ab {v}", className="info-threshold__visitors"),
                        html.Span("Besucher/h", className="info-threshold__unit"),
                        html.Span(f"{st} MA", className="info-threshold__staff"),
                    ])
                    for v, st in [(0, 1), (20, 2), (50, 3), (80, 4),
                                  (120, 5), (160, 6), (200, 7)]
                ]),
            ]),
            html.Div(className="card", children=[
                html.Div(className="card__header", children=[
                    html.Span("checklist", className="material-symbols-outlined card__header-icon"),
                    "Daten-Status",
                ]),
                html.Div(className="model-status", children=_status_rows()),
                html.Div(className="info-modal__note", children=[
                    html.Span("lightbulb", className="material-symbols-outlined"),
                    html.Span(_status_note()),
                ]),
            ]),
        ]),

        html.Div(className="card model-confidence", children=[
            html.Div(className="card__header", children=[
                html.Span("query_stats", className="material-symbols-outlined card__header-icon"),
                "Unsicherheit & Konfidenzband",
            ]),
            html.P(
                "Jede Prognose ist eine Schätzung. Das Konfidenzband (±15 %) im "
                "Prognose-Chart zeigt den Bereich, in dem der tatsächliche Wert "
                "voraussichtlich liegt. Ein breites Band bedeutet höhere Unsicherheit – "
                "die Personalplanung sollte dann vorsichtiger interpretiert werden.",
                className="model-confidence__text",
            ),
        ]),
    ])
