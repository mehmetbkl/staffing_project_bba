# Projektskizze – Open Data Staffing

**PROJEKTSKIZZE**

# Open Data für Staffing-Entscheidungen im Einzelhandel

| | |
|---|---|
| **Modul** | Business Analytics – Teamprojekt |
| **Hochschule** | THWS – Technische Hochschule Würzburg-Schweinfurt |
| **Semester** | SoSe 2026 |
| **Team** | Wladislaw Saydullaev, Mehmet Bekler, Nico Hirsch, David Grünewald, Antonio Sicaja |

---

## 1 Ausgangslage

Im stationären Einzelhandel stellt die optimale Personalbesetzung eine zentrale Herausforderung dar. Zu wenig Personal führt zu langen Wartezeiten und entgangenen Umsätzen; eine Überbesetzung erhöht die Personalkosten unnötig. Traditionell basieren Schichtpläne auf Erfahrungswerten und starren Regeln, die externe Einflussfaktoren wie Wetter, Feiertage, lokale Events oder Ferienzeiten nur unzureichend berücksichtigen.

Gleichzeitig steht eine wachsende Menge an Open Data zur Verfügung: Wetterdienste, öffentliche Veranstaltungskalender, Ferien- und Feiertagsregister sowie demografische und standortbezogene Daten. Dieses Projekt untersucht, wie sich solche frei zugänglichen Quellen systematisch nutzen lassen, um die Nachfrageprognose und damit die Personaleinsatzplanung im Einzelhandel datengestützt zu verbessern.

---

## 2 Projektziele

Das Projekt verfolgt drei aufeinander aufbauende Ziele:

| **Nr.** | **Ziel** | **Beschreibung** |
|---|---|---|
| Z1 | Datenlandschaft kartieren | Identifikation und Bewertung relevanter Open-Data-Quellen (Wetter, Events, Feiertage, Mobilität, Demografie) hinsichtlich Verfügbarkeit, Granularität und Lizenz. |
| Z2 | Prognosemodell entwickeln | Aufbau eines Modells, das auf Basis der identifizierten Datenquellen die erwartete Kundenfrequenz bzw. Nachfrage auf Tages-/Schichtebene prognostiziert. |
| Z3 | Staffing-Empfehlung ableiten | Ableitung konkreter Schichtbesetzungsempfehlungen aus der Prognose, visualisiert in einem interaktiven Dashboard/Plan. |

---

## 3 Geplante Endprodukte

Folgende Artefakte werden im Rahmen des Projekts erstellt:

### 3.1 Datenpipeline

Ein reproduzierbarer ETL-Prozess, der Open-Data-Quellen abruft, bereinigt und in einer strukturierten Datenschicht (z. B. DuckDB oder PostgreSQL) ablegt.

### 3.2 Prognosemodell

Ein Machine-Learning-Modell (z. B. Random Forest, XGBoost oder Prophet), das die erwartete Kundenfrequenz auf Tages- bzw. Schichtebene vorhersagt. Features umfassen unter anderem Wetterdaten, Wochentag, Ferien-/Feiertagsindikatoren und Event-Distanzmaße.

### 3.3 Dashboard

Ein interaktives Dashboard (Plotly Dash), das die Prognose visualisiert und Staffing-Empfehlungen übersichtlich darstellt. Filterfunktionen ermöglichen die Auswahl nach Standort, Zeitraum und Szenario.

### 3.4 Dokumentation & Präsentation

Eine schriftliche Projektdokumentation sowie eine Abschlusspräsentation, die Methodik, Ergebnisse und Limitationen zusammenfassen.

> Ggf. ein eigenes Neuronales Netz aufbauen.

---

## 4 Methodik & Architektur

Das Projekt gliedert sich in vier Phasen:

- **Exploration & Datenerhebung** – Systematische Recherche verfügbarer Open-Data-APIs und Datensätze; Bewertung nach Qualität, Aktualität und Nutzungslizenz.
- **Datenintegration & Feature Engineering** – Aufbau der ETL-Pipeline; Verknüpfung heterogener Quellen über gemeinsame Schlüssel (Datum, Standort); Erstellung abgeleiteter Merkmale.
- **Modellierung & Evaluation** – Training und Validierung des Prognosemodells; Vergleich verschiedener Ansätze (Baseline vs. ML); Metriken: MAE, RMSE, MAPE.
- **Dashboard & Staffing-Logik** – Umsetzung des Dashboards; Implementierung der Staffing-Empfehlung als regelbasiertes Mapping (Prognose → Mitarbeiterzahl).

---

## 5 Open-Data-Quellen

Die folgende Tabelle gibt einen ersten Überblick über potenziell relevante Datenquellen. Die finale Auswahl erfolgt in Phase 1.

| **Kategorie** | **Quelle** | **Granularität** | **Zugang** |
|---|---|---|---|
| Wetter | Open-Meteo | Stündlich / Standort / Forecast | API |
| Feiertage & Ferien | Python Paket `holidays` | Bundesland | `pip install holidays` |
| Veranstaltungen | Open.data.würzburg | Event-Level / Stadt | API, Open Data Portal |
| Mobilität | Google Popular Times / Hystreet | Stündlich / Standort | API, Scraping |
| Demografie & Standort | Destatis / Regionalstatistik | Jährlich / Gemeinde | CSV, REST |

### Veranstaltungen

- ZDI Eventfeed (ergänzend): [opendata.wuerzburg.de – eventfeed](https://opendata.wuerzburg.de/explore/dataset/eventfeed/table/?flg=en-us)

### Mobilität / Passantenzählung

- Stundendaten (seit 2024, 3 Stationen): [opendata.wuerzburg.de – passantenzaehlung_stundendaten](https://opendata.wuerzburg.de/explore/dataset/passantenzaehlung_stundendaten/)
- Tagesdaten (seit 2020, 3 Stationen): [opendata.wuerzburg.de – passantenzaehlung_tagesdaten](https://opendata.wuerzburg.de/explore/dataset/passantenzaehlung_tagesdaten/?flg=en-us)
- Schönbornstraße stündlich (längste Reihe, seit 2019): [opendata.wuerzburg.de – passantenzaehlung_schoenbornstrasse](https://opendata.wuerzburg.de/explore/dataset/passantenzaehlung_schoenbornstrasse/?flg=en-us)
- Monatsübersicht (Vergleich 3 Standorte): [opendata.wuerzburg.de – passantenzaehlung_wuerzburg](https://opendata.wuerzburg.de/explore/dataset/passantenzaehlung_wuerzburg/analyze/?flg=de-de)

### Demografie & Standort

- Hauptwohnsitz nach Altersgruppen pro Stadtbezirk: [wuerzburg.opendatasoft.com – stadtbezirke_hauptwohnsitz_altersgruppen](https://wuerzburg.opendatasoft.com/explore/dataset/stadtbezirke_hauptwohnsitz_altersgruppen/?flg=de-de)
- Durchschnittsalter pro Stadtbezirk: [opendata.wuerzburg.de – stadtbezirke_durchschnittsalter](https://opendata.wuerzburg.de/explore/dataset/stadtbezirke_durchschnittsalter/table/?flg=en-us)
- Wohnberechtigte nach Altersgruppen: [opendata.wuerzburg.de – wohnberechtigte_altersgruppen](https://opendata.wuerzburg.de/explore/dataset/wohnberechtigte_altersgruppen/?flg=de-de)

### 5.3 Interne Unternehmensdaten

Das Team befindet sich aktuell im Austausch mit einem Einzelhandelsunternehmen, um Zugang zu internen Daten zu erhalten. Angestrebt werden insbesondere bestehende Schichtpläne und Personalbesetzungsdaten sowie Kassendaten mit Zeitstempeln zur Bestimmung von Stoßzeiten. Diese internen Daten würden es ermöglichen, das Prognosemodell nicht nur auf Passantenfrequenzen zu trainieren, sondern direkt auf tatsächliche Geschäftskennzahlen zu kalibrieren. Sollte eine Datenbereitstellung im Projektzeitraum nicht realisierbar sein, wird das Modell ausschließlich auf Basis der Open-Data-Quellen entwickelt und die interne Validierung als Ausblick dokumentiert.

---

## 6 Referenzen

### 6.1 Praxisbeispiele & Industrie

- **Walmart Labs – Nachfrageprognose:** Einsatz von ML-Modellen zur Vorhersage der Kundenfrequenz unter Einbeziehung von Wetter- und Event-Daten (Kaggle-Wettbewerb als Referenz).
- **Hystreet.com:** Open-Data-Plattform für Passantenfrequenzen in deutschen Innenstädten – potenziell als Ground-Truth für Modellvalidierung nutzbar.
- **GovData.de / EU Open Data Portal:** Zentrale Plattformen für öffentliche Datensätze in Deutschland und Europa.
- **DWD Climate Data Center:** Frei zugängliche historische und aktuelle Wetterdaten des Deutschen Wetterdienstes.

### 6.2 Technologie-Stack

| **Bereich** | **Werkzeuge** |
|---|---|
| Programmiersprache | Python 3.11+ |
| Datenbank / Storage | DuckDB (lokal, Medallion-Architektur) oder PostgreSQL |
| ETL & Daten | pandas, requests, schedule |
| Modellierung | scikit-learn, XGBoost, Prophet, statsmodels (eigenes ANN) |
| Visualisierung | Plotly Dash |
| Versionierung | Git / GitHub |

---

## 7 Zeitplan (vorläufig)

| **KW** | **Phase** | **Aktivitäten** | **Meilenstein** |
|---|---|---|---|
| 1–2 | Exploration | Quellenrecherche, API-Tests, Datenqualitätsprüfung | Datenquellen-Katalog |
| 3–4 | Datenintegration | Pipeline-Aufbau, Feature Engineering, Datenbankdesign | Gold-Layer bereit |
| 5–7 | Modellierung | Modelltraining, Hyperparameter-Tuning, Evaluation | Modell validiert |
| 8–9 | Dashboard | UI-Aufbau, Staffing-Logik, Testing | Dashboard live |
| 10–11 | Dokumentation | Bericht, Präsentation, Code-Cleanup | Abgabe |

---

## 8 Verteilung individueller Verantwortung

Die Aufgabenverteilung orientiert sich an den Projektphasen und individuellen Stärken. Jedes Teammitglied übernimmt eine Hauptverantwortung und unterstützt in mindestens einem weiteren Bereich.

| **Rolle** | **Person** | **Hauptverantwortung** | **Unterstützt bei** |
|---|---|---|---|
| **Data Engineer** | Wladislaw Saydullaev | ETL-Pipeline, API-Anbindung, Datenqualitätssicherung | Nico, Mehmet |
| **Data Scientist** | Nico Hirsch | Prognosemodell, Feature Engineering, Evaluation & Metriken | Wladislaw |
| **Dashboard Dev** | Mehmet Bekler | Dashboard-Entwicklung (Plotly Dash), Staffing-Logik, UX | Nico, Wladislaw |
| **Research & Doku** | Antonio Sicaja | Quellenrecherche, Literaturreview, Projektdokumentation, Abschlussbericht | David |
| **PM & Präsentation** | David Grünwald | Projektkoordination, Sprint-Planung, Abschlusspräsentation, Stakeholder-Kommunikation | Toni |

Die Zusammenarbeit wird über ein gemeinsames GitHub-Repository organisiert. Wöchentliche Stand-ups stellen sicher, dass Abhängigkeiten frühzeitig erkannt und Blockaden zeitnah gelöst werden. Jedes Teammitglied dokumentiert seine Arbeit fortlaufend im Repository-Wiki.

---

## 9 Risiken & Gegenmaßnahmen

| **Risiko** | **Auswirkung** | **Gegenmaßnahme** |
|---|---|---|
| API-Verfügbarkeit / Rate Limits | Datenlücken, Pipeline-Abbruch | Lokaler Cache, Fallback-Quellen, Bulk-Downloads |
| Fehlende Ground-Truth-Daten | Modellvalidierung erschwert | Hystreet-Daten als Proxy; synthetische Testdaten |
| Heterogene Datenformate | Hoher Integrationsaufwand | Frühzeitige Schema-Definition, Validierungsregeln |
| Scope Creep | Zeitplan-Überschreitung | MVP-Ansatz: erst ein Standort, dann skalieren |

---

## 10 Nächste Schritte

- Teammitglieder und Rollen final zuordnen
- GitHub-Repository anlegen und Grundstruktur aufsetzen
- Open-Data-Quellen sichten und erste API-Tests durchführen
- Referenzstadt / Beispielstandort für den Prototyp festlegen
- Kick-off-Meeting und erste Sprint-Planung durchführen