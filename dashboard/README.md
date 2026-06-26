# StaffCast Dashboard

Interaktives Dash-Frontend für das Open-Data-Staffing-Projekt (THWS SoSe 2026).

---

## Schnellstart

```bash
# 1. In den dashboard-Ordner wechseln
cd dashboard

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. Dashboard starten
python app.py
```

Aufruf im Browser: **http://localhost:8050**

---

## Projektstruktur

```
dashboard/
├── app.py                        # Einstiegspunkt
├── requirements.txt
│
├── assets/
│   ├── theme.css                 # Design Tokens (Farben, Typografie, Abstände)
│   └── styles.css                # Komponentenklassen
│
├── layouts/
│   ├── dashboard.py              # Haupt-Layout (App-Shell)
│   ├── sidebar.py                # Linke Navigation
│   ├── navbar.py                 # Obere Leiste
│   ├── weather_widget.py         # Wetter-Karte
│   ├── summary_widget.py         # Tagesübersicht (dunkle Karte)
│   ├── forecast_chart.py         # Plotly-Diagramm
│   └── staffing_actions.py       # Maßnahmenliste
│
├── callbacks/
│   ├── weather_callbacks.py      # Auto-Refresh Wetterdaten
│   ├── chart_callbacks.py        # Diagramm-Update
│   └── ui_callbacks.py           # Button-Interaktionen
│
├── services/
│   ├── weather_service.py        # Open-Meteo-Anbindung
│   └── forecast_service.py       # Prognose-Platzhalter (→ ANN)
│
└── utils/
    ├── constants.py              # Konfiguration, WMO-Codes, Farben
    └── formatting.py             # Datum, Einheiten, Zahlen
```

---

## Konfiguration

Koordinaten und Start-Datum sind in `utils/constants.py`:

```python
LIBRARY_LAT: float = 49.7913
LIBRARY_LON: float = 9.9534
WEATHER_START_DATE: str = "2025-04-24"
```

---

## ANN-Modell einbinden (für Nico)

Sobald `futureexpert_forecast.py` bereit ist, in `services/forecast_service.py`
die Funktion `get_placeholder_forecast` ersetzen:

```python
# Vorher (Platzhalter):
from services.forecast_service import get_placeholder_forecast
forecast = get_placeholder_forecast()

# Nachher (echtes Modell):
from futureexpert_forecast import get_forecast
forecast = get_forecast(date=target_date)
```

Die `DailySummary`- und `ForecastPoint`-Dataclasses definieren das erwartete
Interface – das Modell muss dieselbe Struktur zurückgeben.

---

## Umgebungsvariablen

| Variable | Standard | Beschreibung              |
|----------|----------|---------------------------|
| `PORT`   | `8050`   | HTTP-Port                 |
| `DEBUG`  | `true`   | Dash Hot-Reload aktivieren |

```bash
PORT=8080 DEBUG=false python app.py
```

---

## Architekturregeln

- Keine Datei > 300 Zeilen
- Kein `style={}` in Komponenten (Ausnahme: minimale Inline-Größen)
- Farben ausschließlich über CSS-Variablen
- Callbacks registrieren über `register_*_callbacks(app)`
- Neue Widgets → neue Datei in `layouts/`, neuer Callback in `callbacks/`

## Datenstand & Platzhalter

### Echte Anbindung (Live-Daten)

**Wetter-Widget (Prognose-Seite)**

- Temperatur, Icon, Beschreibung, Wind, Regen, Bewölkung → Live von `api.open-meteo.com`
- Stundenvorschau (6 Slots) → Live von `api.open-meteo.com`
- Refresh alle 15 Minuten automatisch

Das ist die einzige echte externe Datenquelle im System.

---

### Platzhalter (hardcodiertes Tagesprofil)

Alles andere kommt aus `get_placeholder_forecast()` in `services/forecast_service.py`. Das ist ein fester Array:

```python
_profile = [15, 25, 45, 75, 90, 85, 100, 110, 95, 80, 70, 60, 45, 30]
```

Konkret betroffen:

| Angezeigtes Element | Quelle |
|---|---|
| Prognose-Chart (Balken) | Dieser Array |
| Prognose-Chart (Linie, Mitarbeiter) | Staffing-Schwellenwerte auf diesem Array |
| Konfidenzband | ±15 % auf diesem Array |
| Tagesübersicht: „925 Besucher" | Summe des Arrays |
| Tagesübersicht: „42 h" | Staffing-Stunden aus dem Array |
| Tagesübersicht: „–12 %" | Hardcodiert in `forecast_service.py` |
| Dashboard: alle 4 KPI-Karten | Berechnet aus demselben Array |
| Empfohlene Maßnahmen | Regelbasiert auf demselben Array |

---

### Was fehlt, damit alles echt wird

**Kurzfristig (ohne Nicos Modell):** Die Bibliotheksdaten aus NeonDB (`raw.library_visitors`) könnten direkt in den `forecast_service` fließen — dann wären zumindest die historischen Besucherzahlen echt, auch wenn noch keine Prognose stattfindet.

**Sobald Nicos Modell fertig ist:** `get_placeholder_forecast()` in `forecast_service.py` durch den Aufruf von `futureexpert_forecast.py` ersetzen. Das Interface (`DailySummary`, `ForecastPoint`) bleibt identisch — das ist der einzige Punkt, der geändert werden muss.