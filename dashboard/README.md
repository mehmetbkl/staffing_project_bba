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
│   ├── db.py                     # Zentrale NeonDB-Anbindung (graceful Fallback)
│   ├── weather_service.py        # Open-Meteo-Anbindung
│   ├── forecast_service.py       # Prognose: gold.predictions → CSV → Demo
│   ├── history_service.py        # Historie aus raw.library_visitors / raw.weather
│   └── shift_service.py          # Schichtplan aus staff-Schema (Fallback employees.py)
│
├── data/
│   └── employees.py              # DB-Loader (staff.*) + statischer Fallback
│
└── utils/
    ├── constants.py              # Konfiguration, WMO-Codes, Farben, Schwellenwerte
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

## Prognose-Anbindung

Der `forecast_service` zieht die Prognose automatisch aus der besten verfügbaren
Quelle (kein ANN):

1. **`gold.predictions`** – Tagesprognose aus dem Modell (futureEXPERT oder die
   saisonale Baseline, siehe `models(Nico)/`). Bevorzugt.
2. **`models(Nico)/forecast_besucher.csv`** – CSV-Ausgabe desselben Modells.
3. **Demo-Profil** – festes Tagesprofil, falls weder DB noch CSV verfügbar.

Die Tagesprognose wird über ein typisches Öffnungszeit-Profil (8–21 Uhr) auf
Stunden verteilt. Das Interface (`DailySummary`, `ForecastPoint`) bleibt für alle
Aufrufer identisch – egal aus welcher Quelle die Daten stammen.

Damit eine neue Prognose live erscheint, schreibt das Modell nach
`gold.predictions` (siehe `models(Nico)/forecast_db.py`). Die Personalempfehlung
landet zusätzlich in `gold.staffing_recommendations`.

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

## Datenstand

Jeder Service folgt demselben Muster: **echte DB-/API-Daten, wenn verfügbar,
sonst ein dokumentierter Demo-Fallback.** Welche Quelle gerade aktiv ist, zeigen
die Banner auf den Seiten sowie der Info-Dialog (Topbar).

| Bereich | Live-Quelle | Fallback |
|---|---|---|
| Wetter (Prognose-Seite) | `api.open-meteo.com`, Refresh alle 15 min | Fehlermeldung |
| Historie & Trends | `raw.library_visitors`, `raw.weather` (NeonDB) | Demo-Profil |
| Besucher-Prognose | `gold.predictions` → sonst Modell-CSV | Demo-Tagesprofil |
| Personalempfehlung | Regel auf Prognose + `gold.staffing_recommendations` | – |
| Schichtplan / Personal | `staff.employees`, `staff.shifts` (NeonDB) | `data/employees.py` |

Die DB-Anbindung läuft über `services/db.py` und liest `DATABASE_URL_ETL`
aus der `.env` im Projekt-Root. Ist keine Verbindung möglich, läuft das gesamte
Dashboard im Demo-Modus weiter.