# Open Data für Staffing-Entscheidungen im Einzelhandel

Business Analytics Teamprojekt, THWS Würzburg-Schweinfurt, SoSe 2026.
Details zu Zielen, Methodik und Zeitplan: siehe [`Projektskizze.md`](Projektskizze.md).

Das Projekt prognostiziert die Kundenfrequenz der Stadtteilbücherei Hubland auf Basis
offener Wetterdaten und Kalenderdaten (Feiertage/Ferien) und leitet daraus
Personalbesetzungs-Empfehlungen ab, die in einem interaktiven Dashboard dargestellt werden.

---

## 1 Architekturüberblick

```
                 ┌──────────────────┐
  Open-Meteo  →  │                  │
  holidays    →  │   ETL-Pipeline   │  →  NeonDB (Medallion: raw → processed → gold)
  Bibliothek  →  │   (etl/)         │
                 └──────────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │  Prognosemodell  │  →  gold.predictions
                 │  (models(Nico)/) │  →  gold.staffing_recommendations
                 └──────────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │    Dashboard     │  ←  liest aus gold.* / Fallback-CSV/Demo
                 │   (dashboard/)   │
                 └──────────────────┘
```

Jede Komponente hat ihre eigene, ausführliche README:

| Komponente | Verantwortlich | Doku |
|---|---|---|
| ETL-Pipeline | Wladislaw Saydullaev | [`etl/README.md`](etl/README.md) |
| Prognosemodell | Nico Hirsch | [`models(Nico)/`](models(Nico)/) |
| Dashboard | Mehmet Bekler | [`dashboard/README.md`](dashboard/README.md) |
| Geplanter täglicher Lauf | Wladislaw Saydullaev | [`scripts/README.md`](scripts/README.md) |
| Research & Dokumentation | Antonio Sicaja | [`docs/`](docs/) |
| Projektkoordination | David Grünwald | [`Projektskizze.md`](Projektskizze.md) |

---

## 2 Quickstart

> **Python-Version:** getestet mit **Python 3.10 – 3.13**, empfohlen **3.12** (wie in
> der CI). Bitte immer eine **virtuelle Umgebung** nutzen, damit die Versionen
> sauber isoliert sind. Prüfen mit `python --version`.

```bash
# 1. Repository klonen
git clone https://github.com/mehmetbkl/staffing_project_bba.git
cd staffing_project_bba

# 2. Virtuelle Umgebung anlegen und aktivieren
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. pip aktualisieren (wichtig – alte pip-Versionen finden neue Wheels nicht)
python -m pip install --upgrade pip

# 4. Abhängigkeiten installieren
pip install -r requirements.txt

# 5. .env anlegen (siehe .env.example) – DB-Zugangsdaten eintragen

# 6. ETL einmalig ausführen
python -m etl.pipeline

# 7. Dashboard starten
cd dashboard
pip install -r requirements.txt
python app.py
```

Dashboard danach erreichbar unter `http://localhost:8050`.

> **Optional – futureEXPERT-Modell:** Das alternative Prognosemodell
> (`models(Nico)/futureexpert_forecast.py`) benötigt zusätzlich das Paket
> `futureexpert`, das intern `numpy<2` verlangt und deshalb **nur mit Python
> 3.9 – 3.12** läuft. Installation nur bei Bedarf:
> `pip install -r "models(Nico)/requirements.txt"`. Für ETL, Dashboard und die
> Baseline-Prognose wird es **nicht** gebraucht.

---

## 3 Datenbasis

Eine vollständige Bewertung aller geprüften Open-Data-Quellen (Verfügbarkeit, Lizenz,
Granularität, Datenqualität) findet sich im [Quellenkatalog](docs/Quellenkatalog.md).
Kurzfassung:

| Quelle | Rolle | Tabelle |
|---|---|---|
| Open-Meteo | Wetter-Feature | `raw.weather` |
| `holidays`-Paket | Kalender-Feature | `processed.holidays` |
| Stadtteilbücherei Hubland | Zielvariable | `raw.library_visitors` |

---

## 4 Projektstruktur

```
├── docs/                  # Quellenkatalog, Literaturreview, Abschlussbericht
├── etl/                   # Datenpipeline
├── models(Nico)/          # Prognosemodelle (Baseline & futureEXPERT)
├── dashboard/             # Plotly-Dash-Frontend
├── db/                    # SQL-Schemas (Medallion-Architektur)
├── scripts/               # Automatisierter täglicher ETL-Lauf
├── Projektskizze.md        # Ursprüngliche Projektskizze
└── CONTRIBUTING.md         # Git-Workflow & Coding-Guidelines
```

---

## 5 Team & Rollen

| Rolle | Person |
|---|---|
| Data Engineer | Wladislaw Saydullaev |
| Data Scientist | Nico Hirsch |
| Dashboard Dev | Mehmet Bekler |
| Research & Doku | Antonio Sicaja |
| PM & Präsentation | David Grünwald |

Details zur Aufgabenverteilung: [`Projektskizze.md`](Projektskizze.md#8-verteilung-individueller-verantwortung).

---




