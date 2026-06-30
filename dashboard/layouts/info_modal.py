"""
layouts/info_modal.py
Globaler Info-Dialog: erklärt Datenquellen, Prognose-Basis und Methodik.
Wird über den Info-Button in der Topbar geöffnet (siehe ui_callbacks).
"""

from __future__ import annotations
from dash import html

from services.db import db_available
from services.forecast_service import get_forecast, forecast_source
from services.history_service import get_last_30_days, is_live as history_live


def _section(icon: str, title: str, body) -> html.Div:
    return html.Div(
        className="info-modal__section",
        children=[
            html.Div(
                className="info-modal__section-head",
                children=[
                    html.Span(icon, className="material-symbols-outlined"),
                    html.Span(title),
                ],
            ),
            html.Div(body, className="info-modal__section-body"),
        ],
    )


def _source_row(label: str, value: str, live: bool) -> html.Div:
    badge_cls = (
        "info-source__badge info-source__badge--live"
        if live else "info-source__badge info-source__badge--demo"
    )
    badge_text = "Live" if live else "Platzhalter"
    return html.Div(
        className="info-source",
        children=[
            html.Span(label, className="info-source__label"),
            html.Span(value, className="info-source__value"),
            html.Span(badge_text, className=badge_cls),
        ],
    )


def _live_state_note(db_ok: bool, hist_live: bool, fc_src: str) -> str:
    if not db_ok:
        return ("Aktueller Stand: Wetter ist live (Open-Meteo). Die NeonDB ist gerade "
                "nicht erreichbar, daher laufen Besucherzahlen und Prognose über Demo-Daten. "
                "Sobald die DB verbunden ist, wird automatisch umgeschaltet.")
    parts = ["Wetter ist live (Open-Meteo)."]
    parts.append("Historie: " + ("live aus der NeonDB." if hist_live
                                  else "noch Demo (raw.library_visitors leer)."))
    if fc_src == "db":
        parts.append("Prognose: live aus gold.predictions.")
    elif fc_src == "csv":
        parts.append("Prognose: aus der Modell-CSV.")
    else:
        parts.append("Prognose: noch Demo-Profil.")
    return "Aktueller Stand: " + " ".join(parts)


def render_info_modal() -> html.Div:
    # Datenlage einmalig beim Aufbau ermitteln
    get_last_30_days()
    get_forecast()
    hist_live = history_live()
    fc_src = forecast_source()
    pred_live = fc_src in ("db", "csv")
    pred_value = {
        "db":   "NeonDB · gold.predictions",
        "csv":  "Modell-CSV · forecast_besucher.csv",
        "demo": "Demo-Profil (Modell folgt)",
    }[fc_src]

    from data.employees import employees_source
    staff_src = employees_source()
    staff_live = staff_src == "db"
    staff_value = ("NeonDB · staff.employees" if staff_live
                   else "Fallback · data/employees.py")

    return html.Div(
        id="info-modal",
        className="info-modal info-modal--hidden",
        children=[
            html.Div(id="info-modal-backdrop", className="info-modal__backdrop"),
            html.Div(
                className="info-modal__dialog",
                children=[
                    html.Div(
                        className="info-modal__header",
                        children=[
                            html.Div(
                                className="info-modal__title",
                                children=[
                                    html.Span("info", className="material-symbols-outlined"),
                                    "Worauf basiert diese Prognose?",
                                ],
                            ),
                            html.Button(
                                id="info-modal-close",
                                className="info-modal__close",
                                n_clicks=0,
                                children=html.Span(
                                    "close", className="material-symbols-outlined"
                                ),
                            ),
                        ],
                    ),
                    html.Div(
                        className="info-modal__content",
                        children=[
                            html.P(
                                "StaffCast schätzt die zu erwartende Besucherfrequenz "
                                "der Bibliothek am Hubland (Würzburg) und leitet daraus "
                                "eine stündliche Personalempfehlung ab. Ziel ist es, "
                                "Über- und Unterbesetzung frühzeitig sichtbar zu machen.",
                                className="info-modal__lead",
                            ),
                            _section(
                                "database",
                                "Datenquellen",
                                [
                                    _source_row(
                                        "Wetter (aktuell + Stundenvorschau)",
                                        "Open-Meteo API", live=True,
                                    ),
                                    _source_row(
                                        "Historische Besucherzahlen",
                                        "NeonDB · raw.library_visitors", live=hist_live,
                                    ),
                                    _source_row(
                                        "Besucher-Prognose",
                                        pred_value, live=pred_live,
                                    ),
                                    _source_row(
                                        "Schichtplan",
                                        staff_value, live=staff_live,
                                    ),
                                ],
                            ),
                            _section(
                                "query_stats",
                                "Methodik",
                                html.Div([
                                    html.P(
                                        "Die Prognose kombiniert kalendarische Merkmale "
                                        "(Wochentag, Tageszeit, Feiertage/Ferien) mit "
                                        "Wetterfaktoren. Aus der geschätzten Besucherzahl "
                                        "wird über feste Schwellenwerte die "
                                        "empfohlene Mitarbeiterzahl bestimmt."
                                    ),
                                    html.P(
                                        "Das Konfidenzband (±15 %) zeigt die "
                                        "Unsicherheit der Schätzung. Je breiter das Band, "
                                        "desto vorsichtiger sollte die Personalplanung "
                                        "interpretiert werden.",
                                        className="info-modal__muted",
                                    ),
                                ]),
                            ),
                            _section(
                                "rule",
                                "Personal-Schwellenwerte",
                                html.Div(
                                    className="info-thresholds",
                                    children=[
                                        html.Div(
                                            className="info-threshold",
                                            children=[
                                                html.Span(f"ab {v}", className="info-threshold__visitors"),
                                                html.Span("Besucher/h", className="info-threshold__unit"),
                                                html.Span(f"{s} MA", className="info-threshold__staff"),
                                            ],
                                        )
                                        for v, s in [
                                            (0, 1), (20, 2), (50, 3),
                                            (80, 4), (120, 5), (160, 6), (200, 7),
                                        ]
                                    ],
                                ),
                            ),
            html.Div(
                                className="info-modal__note",
                                children=[
                                    html.Span("lightbulb", className="material-symbols-outlined"),
                                    html.Span(_live_state_note(db_available(), hist_live, fc_src)),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
