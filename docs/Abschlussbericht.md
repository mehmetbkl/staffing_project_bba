# Abschlussbericht – Open Data für Staffing-Entscheidungen im Einzelhandel

**Team:** Wladislaw Saydullaev, Nico Hirsch, Mehmet Bekler, Antonio Sicaja, David Grünwald
**Modul:** Business Analytics – Teamprojekt, THWS, SoSe 2026
**Status:** Teilentwurf – enthält die bereits abgeschlossenen Kapitel. Ergänzungen zu
Modellgüte, ETL-Pipeline, Feature Engineering und Staffing-Logik folgen, sobald die
entsprechenden Ergebnisse vorliegen.

---

## Ausgangslage und Zielsetzung

Personaleinsatzplanung im Einzelhandel erfolgt häufig auf Basis von Erfahrungswerten statt
auf einer belastbaren Datengrundlage, was zu Über- oder Unterbesetzung führt. Das Projekt
untersucht, wie sich frei verfügbare Open-Data-Quellen – insbesondere Wetter- und
Kalenderdaten – nutzen lassen, um die Kundenfrequenz eines Standorts vorherzusagen und daraus
konkrete Staffing-Empfehlungen abzuleiten. Verfolgt werden drei Projektziele: die Kartierung
der verfügbaren Datenlandschaft (Z1), der Aufbau eines Prognosemodells für die Besucherzahl
(Z2) sowie die Ableitung einer Personalempfehlung aus dieser Prognose (Z3), dargestellt in
einem interaktiven Dashboard.

---

## Stand der Forschung

Eine ausführliche Aufarbeitung befindet sich im [Literaturreview](Literaturreview.md).
Die wichtigsten Erkenntnisse für das Projekt:

- Wetter hat einen signifikanten, aber saison- und standortabhängigen Effekt auf die
  Kundenfrequenz im Einzelhandel; der Effekt unterscheidet sich deutlich zwischen
  Innenstadt- und Randlagen sowie zwischen Produktkategorien.
- Kalendereffekte wie Feiertage und Schulferien gelten in der Praxisliteratur als mindestens
  gleichrangig zu Wettereffekten und sollten als eigene Feature-Gruppe modelliert werden.
- Praxisbeispiele großer Einzelhändler (u. a. Ross Stores, Dick's Sporting Goods) bestätigen,
  dass die systematische Nutzung von Wetterdaten für Personal- und Sortimentsentscheidungen
  dem aktuellen Stand der Branchenpraxis entspricht.
- Aus diesen Erkenntnissen ergibt sich die methodische Konsequenz, dass ein
  Machine-Learning-Ansatz einer rein linearen Baseline vorzuziehen ist, da die
  Zusammenhänge zwischen Wetter, Kalender und Nachfrage nicht linear sind.

---

## Datenquellen

Die vollständige Bewertung aller geprüften Open-Data-Quellen – inklusive Verfügbarkeit,
Lizenz, Granularität und Datenqualität – befindet sich im [Quellenkatalog](Quellenkatalog.md).
Final in der ETL-Pipeline genutzt werden drei Quellen:

| Quelle | Rolle im Projekt | Tabelle |
|---|---|---|
| Open-Meteo | Prädiktor (Wetter-Feature) | `raw.weather` |
| `holidays`-Paket | Prädiktor (Kalender-Feature) | `processed.holidays` |
| Bibliotheksbesucher Hubland | Zielvariable (Ground Truth) | `raw.library_visitors` |

Mehrere weitere Quellen wurden geprüft, aber bewusst nicht verwendet – u. a. Event-Daten der
Stadt Würzburg, demografische Daten sowie Hystreet/Google Popular Times als mögliche
Ground-Truth-Alternativen. Die Gründe dafür (Lizenzeinschränkungen, fehlende räumliche
Deckungsgleichheit mit dem Standort Hubland, technische Zugriffsbeschränkungen) sind im
Quellenkatalog im Detail dokumentiert.

---

## Dashboard

Das Dashboard „StaffCast" (Plotly Dash, siehe `dashboard/`) bildet fünf Ansichten ab:

- **Dashboard** – Tagesüberblick mit Besucherzahl, empfohlenen Personalstunden, Peak-Stunde
  und aktueller Schichtbesetzung.
- **Prognose** – Stundengenaue Nachfrageprognose im Abgleich mit empfohlenem Personal,
  inklusive externer Faktoren (Wetter) und automatisch abgeleiteten Maßnahmen
  (z. B. „Spitzenzeit 15:00 Uhr – 4 Mitarbeiter empfohlen").
- **Historie & Trends** – 30-Tage-Besucherverlauf, Ø Besucher je Wochentag, typisches
  Tagesprofil und eine Wetter-Korrelation (Temperatur vs. Besucherzahl).
- **Personalplanung** – Wochen-Schichtplan aller Mitarbeitenden mit Gesamtstunden und
  Besetzung je Wochentag.
- **Modell-Insights** – transparente Erklärung des Datenflusses (Rohdaten → Aufbereitung →
  Prognosemodell → Personalregel → Dashboard), der genutzten Einflussfaktoren (Wochentag,
  Tageszeit, Feiertage/Ferien, Temperatur, Niederschlag, Bewölkung/Wind) sowie der
  regelbasierten Umrechnung von Besucherzahl in Personalempfehlung (z. B. ab 80 Besucher/h
  → 4 Mitarbeitende) und des Konfidenzbands (±15 %) zur Einordnung der Prognoseunsicherheit.

Zum Zeitpunkt dieser Dokumentation liefen Wetterdaten und die Personalregel bereits live;
historische Besucherzahlen und die Modellprognose selbst liefen noch im Demo-/Fallback-Modus,
da die Anbindung an die NeonDB nicht durchgängig verfügbar war. Das Dashboard ist so gebaut,
dass es automatisch auf Live-Daten umschaltet, sobald DB-Verbindung und täglicher ETL-Lauf
(siehe `scripts/README.md`) stehen – am Interface selbst ändert sich dadurch nichts.

---

## Quellenverzeichnis

Siehe [Literaturreview – Quellenverzeichnis](Literaturreview.md#6-quellenverzeichnis) sowie
[Quellenkatalog](Quellenkatalog.md) für alle Datenquellen.
