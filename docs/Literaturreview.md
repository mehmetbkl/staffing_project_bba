# Literaturreview – Open Data & Nachfrageprognose im Einzelhandel

**Verantwortlich:** Antonio Sicaja (Research & Doku)
**Status:** Entwurf – als Grundlage für Kap. 2 „Stand der Forschung" im Abschlussbericht

---

## 1 Einordnung

Dieses Review fasst den Stand der Literatur zu zwei für das Projekt zentralen Fragen zusammen:
(1) Wie stark und auf welche Weise beeinflusst Wetter die Kundenfrequenz und Nachfrage im
stationären Einzelhandel? (2) Welche Methoden werden in Praxis und Forschung eingesetzt, um
aus solchen externen Faktoren Prognosen und Staffing-Entscheidungen abzuleiten?

---

## 2 Wettereinfluss auf Kundenfrequenz und Umsatz

Mehrere Studien belegen einen signifikanten, aber stark kontextabhängigen Zusammenhang
zwischen Wetter und Einzelhandelsnachfrage. Eine Untersuchung auf Basis von Tagesumsätzen
eines großen britischen Filialisten mit über 2.000 Standorten zeigt, dass der Wettereinfluss
im Frühjahr und Sommer am stärksten ausfällt und Wind dabei durchgängig der einflussreichste
Faktor ist; zudem unterscheiden sich Produktkategorien stark in ihrer Wetterabhängigkeit,
wobei Gesundheitslebensmittel am empfindlichsten reagieren.

Für die Kundenfrequenz (Footfall) speziell zeigt eine Studie zu Mode-Einzelhandel, dass Regen
je nach Vertriebskanal gegensätzlich wirkt: In Einkaufszentren steigt die Frequenz bei Regen,
in reinen Straßenlagen sinkt sie – ein Hinweis darauf, dass der Standorttyp (vergleichbar mit
der Frage Innenstadt- vs. Stadtteilstandort im vorliegenden Projekt) eine wichtige Moderatorvariable
ist. Eine Übersichtsarbeit zum Thema kommt zu einem ähnlichen Schluss und stellt fest, dass
Straßenlagen ohne Überdachung deutlich wetteranfälliger sind als überdachte oder
Randlagen-Standorte.

Größenordnungen aus praxisnahen Quellen liefern zusätzliche Anhaltspunkte für die
Modellierung: Niederschlag reduziert die stationäre Kundenfrequenz im Einzelhandel demnach
typischerweise um einen niedrigen bis mittleren zweistelligen Prozentbereich, während er
gleichzeitig digitale Kanäle bzw. Lieferdienste begünstigen kann. Solche Zahlen sind nicht
eins-zu-eins auf den Projektkontext (Bibliotheksbesuch statt Einzelhandelsumsatz) übertragbar,
liefern aber eine Plausibilitätsgröße für die Effektstärke, die im eigenen Modell (Feature
Importance der Wettervariablen, siehe `models(Nico)/`) zu erwarten ist.

---

## 3 Feiertage, Ferien und Events als Nachfragetreiber

Neben Wetter gelten Kalendereffekte (Feiertage, Schulferien, lokale Veranstaltungen) in der
Praxisliteratur als eigenständige, oft noch stärkere Einflussgröße auf Kundenfrequenz und
Personalbedarf. Anbieter im Bereich Demand Planning betonen, dass insbesondere die Kombination
aus Wetterereignissen und Kalenderevents (z. B. Feiertage mit gleichzeitig schlechtem Wetter)
für Einzelhändler besonders schwer zu prognostizieren ist und deshalb explizit als eigene
Feature-Gruppe modelliert werden sollte – ein Ansatz, der sich im vorliegenden Projekt in der
Kombination aus `holidays`-Paket und Wetterdaten in der Gold-Layer-Feature-Tabelle
(`etl/transformers/gold_features.py`) widerspiegelt.

---

## 4 Praxisbeispiele: Weather-driven Demand Forecasting

Große Einzelhändler setzen kommerzielle Wetteranalyse-Plattformen ein, um Personal-, Sortiments-
und Preisentscheidungen an Wettervorhersagen zu koppeln; genannt werden u. a. Ross Stores,
Dick's Sporting Goods und Unilever als Anwender entsprechender Lösungen. Diese Praxisbeispiele
bestätigen den in der Projektskizze (Kap. 6.1) skizzierten Walmart-Ansatz und zeigen, dass die
im Projekt gewählte Grundidee – Wetterdaten systematisch als Prognose-Feature zu nutzen – dem
Stand der Praxis in der Branche entspricht, auch wenn kommerzielle Lösungen i. d. R. zusätzliche,
kostenpflichtige Datenquellen (z. B. AccuWeather Business, Planalytics) statt frei zugänglicher
Open-Data-Quellen nutzen.

---

## 5 Einordnung für das eigene Projekt

Aus dem Literaturüberblick lassen sich drei Implikationen für das Projekt ableiten:

1. **Nichtlinearität und Interaktionseffekte einplanen.** Da die Literatur zeigt, dass
   Wettereffekte je nach Standorttyp und Saison unterschiedlich wirken, ist ein
   Machine-Learning-Ansatz (Random Forest / XGBoost, siehe Projektskizze Kap. 6.2) einer rein
   linearen Baseline vorzuziehen – konsistent mit der im Projekt gewählten Kombination aus
   Baseline- und ML-Modell (`models(Nico)/baseline_forecast.py` vs. `futureexpert_forecast.py`).
2. **Kalendereffekte mindestens so stark gewichten wie Wetter.** Feiertage/Ferien sollten im
   Feature-Set nicht als Nebenvariable, sondern gleichrangig zu Wetterdaten behandelt werden.
3. **Zurückhaltung bei der Übertragbarkeit von Effektgrößen.** Die in der Literatur berichteten
   Prozentwerte stammen überwiegend aus umsatzbasierten Einzelhandelsstudien und sind nicht
   direkt auf Bibliotheksbesuchszahlen übertragbar; sie dienen im Abschlussbericht nur als
   groben Vergleichsmaßstab, nicht als Erwartungswert.

---

## 6 Quellenverzeichnis

- Agnew, M. & Thornes, J. (1995). Weather sensitivity of UK supermarket products. Zitiert nach: *It's the Weather: Quantifying the Impact of Weather on Retail Sales*, Applied Spatial Analysis and Policy, 2021.
- Badorf, F. & Hoberg, K. (2020). Zur Wetterabhängigkeit von Innenstadt- vs. Randlagen-Einzelhandel. Zitiert nach: ebd.
- Martinez-de-Albeniz, V. & Belkaid, F. (2021). Weather Pricing im Modehandel. Zitiert nach: *Here Comes the Sun: Fashion Goods Retailing under Weather Fluctuations*, 2020.
- Studie zu einem britischen Einzelhandelsfilialisten (>2.000 Standorte): *Real-Time Footfall Prediction Using Weather Data: A Case on Retail Analytics*, ResearchGate, 2019.
- *It's the Weather: Quantifying the Impact of Weather on Retail Sales*, Applied Spatial Analysis and Policy, Springer, 2021.
- *Here Comes the Sun: Fashion Goods Retailing under Weather Fluctuations*, 2020.
- *Weather-Driven Demand Forecasting For Optimal Shift Management*, myshyft.com, 2024.
- *How Do Weather Analytics Affect Demand Forecasting in Retail?*, Clarkston Consulting, 2023.
- *Better retail demand planning and forecasting with events*, PredictHQ, 2022.
- Open-Meteo, DWD Climate Data Center, Hystreet.com, GovData.de – als Datenquellen bereits im Quellenkatalog (`docs/Quellenkatalog.md`) dokumentiert.



