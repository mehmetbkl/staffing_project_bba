# Quellenkatalog – Open Data für Staffing-Entscheidungen

**Verantwortlich:** Antonio Sicaja (Research & Doku)
**Status:** Entwurf – bitte nach finaler Datenauswahl aktualisieren (Spalte „Im Projekt genutzt?")
**Bezug:** Projektziel Z1 (Projektskizze, Kap. 2 & 5)

Dieser Katalog dokumentiert alle im Projekt geprüften Open-Data-Quellen und bewertet sie
nach Verfügbarkeit, Granularität, Lizenz und Datenqualität. Er ist die Grundlage für die
Quellenauswahl in der ETL-Pipeline (`etl/sources/`).

---

## 1 Bewertungskriterien

| Kriterium | Beschreibung |
|---|---|
| **Verfügbarkeit** | API / Download, Aktualisierungsfrequenz, Historie |
| **Granularität** | zeitliche und räumliche Auflösung |
| **Lizenz** | Nutzungsbedingungen, Attribution, kommerzielle Nutzung |
| **Datenqualität** | Vollständigkeit, Lücken, Plausibilität |
| **Relevanz** | Eignung als Feature für das Prognosemodell |

---

## 2 Wetterdaten

| | |
|---|---|
| **Quelle** | Open-Meteo (`api.open-meteo.com`) |
| **Zugang** | REST-API, kostenlos, kein API-Key nötig |
| **Granularität** | stündlich, Standort via Lat/Lon (Hubland-Koordinaten: 49.7913 / 9.9534) |
| **Historie** | Archiv-Endpoint zusätzlich zu Forecast-Endpoint |
| **Lizenz** | CC BY 4.0 (Attribution erforderlich) |
| **Datenqualität** | gut, basiert auf mehreren Wettermodellen (u. a. DWD ICON) |
| **Im Projekt genutzt?** |  Ja – `etl/sources/weather.py`, Tabelle `raw.weather` |
| **Anmerkung** | DWD Climate Data Center als alternative/ergänzende Quelle geprüft, aber wegen komplexerer Zugriffsstruktur nicht genutzt. |

---

## 3 Feiertage & Schulferien

| | |
|---|---|
| **Quelle** | Python-Paket `holidays` |
| **Zugang** | `pip install holidays`, lokal, kein API-Call |
| **Granularität** | Bundesland (Bayern), Tagesebene |
| **Lizenz** | MIT-Lizenz, frei nutzbar |
| **Datenqualität** | sehr zuverlässig, gepflegte Community-Bibliothek |
| **Im Projekt genutzt?** |  Ja – `etl/sources/holidays.py`, Tabelle `processed.holidays` |
| **Anmerkung** | Deckt gesetzliche Feiertage ab; Schulferien Bayern ggf. separat zu prüfen/ergänzen. |

---

## 4 Passantenfrequenz / Bibliotheksbesucher

| | |
|---|---|
| **Quelle** | Stadtteilbücherei Hubland (interne Zähldaten als Proxy für Kundenfrequenz) |
| **Zugang** | intern über Projektpartner |
| **Granularität** | stündlich |
| **Lizenz** | projektintern, nicht öffentlich weiterverwendbar |
| **Im Projekt genutzt?** |  Ja – `etl/sources/library.py`, Tabelle `raw.library_visitors` |
| **Anmerkung** | Dient als Zielvariable (Ground Truth) für das Prognosemodell, ersetzt die in der Projektskizze noch offene Frage nach internen Unternehmensdaten. |

---

## 5 Passantenzählung Würzburg (geprüft, nicht genutzt)

| | |
|---|---|
| **Quelle** | opendata.wuerzburg.de – Passantenzählung (Stunden-/Tagesdaten, 3 Stationen, u. a. Schönbornstraße seit 2019) |
| **Zugang** | Open-Data-Portal, CSV/API |
| **Granularität** | stündlich bzw. täglich |
| **Lizenz** | offen (Open-Data-Portal Würzburg) |
| **Datenqualität** | lange Zeitreihe (Schönbornstraße), aber andere Standorte als der Projektstandort (Hubland) |
| **Im Projekt genutzt?** |  Nein – als mögliche Validierungsquelle geprüft, aber räumlich nicht deckungsgleich mit dem Bibliotheksstandort |

---

## 6 Veranstaltungen (Events)

| | |
|---|---|
| **Quelle** | Open.data.würzburg – ZDI Eventfeed |
| **Zugang** | Open-Data-Portal, API |
| **Granularität** | Event-Level, Stadt Würzburg |
| **Lizenz** | offen |
| **Im Projekt genutzt?** |  Nein (Stand aktueller Repo-Stand) |
| **Anmerkung** | Als Feature „Event-Distanzmaß" in der Projektskizze vorgesehen (Kap. 3.2); im finalen Feature-Set (`etl/transformers/gold_features.py`) prüfen, ob umgesetzt. Falls nicht: als Ausblick im Abschlussbericht dokumentieren. |

---

## 7 Demografie & Standort

| | |
|---|---|
| **Quelle** | opendata.wuerzburg.de / wuerzburg.opendatasoft.com (Hauptwohnsitz nach Altersgruppen, Durchschnittsalter pro Stadtbezirk) |
| **Zugang** | Open-Data-Portal, CSV |
| **Granularität** | jährlich, Stadtbezirk |
| **Lizenz** | offen |
| **Im Projekt genutzt?** |  Nein (Stand aktueller Repo-Stand) |
| **Anmerkung** | Eher für standortübergreifende Skalierung relevant (mehrere Filialen); für MVP mit einem Standort (Hubland) von geringerer Priorität – siehe Risikotabelle „Scope Creep" in der Projektskizze. |

---

## 8 Mobilität (Google Popular Times / Hystreet)

| | |
|---|---|
| **Quelle** | Hystreet.com, Google Popular Times |
| **Zugang** | API bzw. Scraping (rechtlich/technisch aufwändiger) |
| **Lizenz** | Hystreet: teils kostenpflichtig / eingeschränkt; Google Popular Times: kein offizielles API, nur Scraping |
| **Im Projekt genutzt?** |  Nein |
| **Anmerkung** | In der Projektskizze (Kap. 6.1) als mögliche Ground-Truth-Referenz genannt; wegen Zugriffsbeschränkungen nicht umgesetzt. Interne Bibliotheksdaten übernehmen stattdessen die Ground-Truth-Funktion (siehe Abschnitt 4). |

---

## 9 Interne Unternehmensdaten

Ursprünglich war laut Projektskizze (Kap. 5.3) der Zugang zu Schichtplan- und Kassendaten
eines Einzelhandelspartners angestrebt. Diese Konstellation wurde im Projektverlauf durch
die Zusammenarbeit mit der Stadtteilbücherei Hubland ersetzt: Die Bibliotheksbesucherdaten
übernehmen die Rolle der internen Ground-Truth-Daten, das `staff`-Schema (`db/03_staff_schema.sql`)
bildet Mitarbeitende und Schichten ab.

---

## 10 Zusammenfassung – finale Datenbasis

| Quelle | Rolle im Projekt | Tabelle |
|---|---|---|
| Open-Meteo | Prädiktor (Feature) | `raw.weather` |
| `holidays`-Paket | Prädiktor (Feature) | `processed.holidays` |
| Bibliotheksbesucher Hubland | Zielvariable (Ground Truth) | `raw.library_visitors` |
| Interne Personal-/Schichtdaten | Staffing-Logik | `staff.*` |


