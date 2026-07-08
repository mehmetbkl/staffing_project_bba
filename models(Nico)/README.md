# Prognosemodelle (Nico Hirsch)

Dieser Ordner enthält den kompletten Forecast-Teil: Besucherprognose für die
Stadtteilbücherei Hubland auf Tages- und Stundenebene, mit zwei Horizonten und
zwei unabhängigen Modellwegen.

## Zwei Horizonte

| Horizont | Reichweite | Wetter-Input | Zweck |
|---|---|---|---|
| **Detail** | 10 Tage | echte Wettervorhersage (Open-Meteo) als Kovariate | Schichtplanung |
| **Grob** | 30 Tage | keine bzw. Klimatologie | Kapazitäts-/Urlaubsplanung |

Die Trennung ist bewusst: Wettermodelle haben nur ~14 Tage Vorhersagekraft.
Im Detail-Horizont verbessert das Wetter die Prognose, darüber hinaus wäre es
eine Schein-Kovariate. Tag 1–10 kommt aus dem Detail-Lauf, Tag 11–30 aus dem
Grob-Lauf – zusammen ergibt das einen konsistenten 30-Tage-Verlauf für
Dashboard und DB (`gold.predictions`, `gold.staffing_recommendations`).

## Module

| Datei | Rolle |
|---|---|
| `weather_forecast.py` | Eigener Wetter-Forecast: Tag 1–15 Open-Meteo-Vorhersage (API-Maximum: 16 Tage inkl. heute), danach 10-Jahres-Klimatologie (±7-Tage-Fenster). Fallback-Kette Forecast → Klimatologie → Persistenz, bricht nie ab. Liefert die Zukunfts-Kovariaten für beide Modellwege. |
| `futureexpert_forecast.py` | **Hauptmodell** über futureEXPERT (prognostica). Der Matcher prüft vorab, ob Temperatur/Niederschlag die Prognose messbar verbessern (Kovariaten-Ranking, Lag 0); der Detail-Forecast nutzt sie dann, der Grob-Forecast läuft univariat. Mit Vorab-Checks, DB-Fallback (DS→ETL) und Aktualitätswarnung. |
| `ml_forecast.py` | **Version 2 ohne futureEXPERT**: Gradient Boosting mit Quantil-Verlust (q 0.1/0.5/0.9 → echtes 80%-Prognoseintervall), Kalender-/Feiertags-/Brückentag-/Lag-/Wetter-Features, rekursive 30-Tage-Prognose. Inklusive Rolling-Origin-Backtest (MAE/RMSE/MAPE + Intervall-Coverage) gegen die Seasonal-Naive-Baseline. |
| `hourly_profile.py` | **Stunden-Forecast** per Top-Down-Disaggregation: empirisches Stundenprofil je Wochentag (Median der Stundenanteile aus raw.library_visitors, umgerechnet nach Europe/Berlin – geschlossene Stunden automatisch 0), das die Tagesprognose auf Stunden verteilt. Fallback: festes 8–21-Uhr-Profil. |
| `baseline_forecast.py` | Seasonal-Naive-Baseline (Median je Wochentag). Referenz für die Modellevaluation, läuft ohne externe Dienste. |
| `forecast_db.py` | Persistenz: schreibt Prognosen und Schicht-Personalempfehlungen idempotent in die Gold-Tabellen; nutzt optional das empirische Stundenprofil. |

## Setup

```bash
pip install -r requirements.txt
```

Ab **Python 3.13** überspringt die requirements.txt das futureexpert-Paket
automatisch (es pinnt `numpy<2`, wofür es dort keine Wheels gibt; der Pin ist
rein konservativ – futureexpert läuft nachweislich mit numpy 2). Dann einmalig:

```bash
pip install futureexpert --no-deps
```

Danach `.env` anlegen (Kopie von `.env.example`) mit den Neon-URLs und
`FUTURE_USER` / `FUTURE_PW`. Einmalig als Admin ausführen:
`db/05_fix_gold_grants.sql` (behebt fehlende gold-Rechte für DB-Writes).

## Ausführen

```bash
# Erst Daten aktualisieren (sonst startet der Forecast in der Vergangenheit)
python -m etl.pipeline

# Hauptmodell (braucht FUTURE_USER / FUTURE_PW in der .env)
python "models(Nico)/futureexpert_forecast.py"

# Version 2 ohne futureEXPERT (inkl. Backtest)
python "models(Nico)/ml_forecast.py"

# Nur den Wetter-Forecast testen
python "models(Nico)/weather_forecast.py"
```

## Ausgaben

Tagesebene: `forecast_besucher.csv` (kombinierte 30 Tage, liest das Dashboard
als Fallback), `forecast_besucher_10d.csv` / `forecast_besucher_30d.csv`
(futureEXPERT-Einzelläufe), `forecast_besucher_ml.csv` (Version 2).
Stundenebene (für die Schichtplanung): `forecast_besucher_stuendlich.csv`
(futureEXPERT) und `forecast_besucher_ml_stuendlich.csv` (Version 2) – je
Öffnungsstunde Prognose inkl. Konfidenzband über die vollen 30 Tage; die
Stundensummen eines Tages ergeben exakt die Tagesprognose. Dazu
`ml_backtest_metrics.csv` (Backtest-Kennzahlen) und `weather_forecast.csv`.
Die Schicht-Personalempfehlungen in `gold.staffing_recommendations` nutzen
dasselbe empirische Stundenprofil (Spitzenstunde je Schicht).

In `gold.predictions` schreiben beide Wege unter eigenem `model_name`
(`futureEXPERT` bzw. `ml-gradient-boosting`) – das Dashboard bevorzugt
futureEXPERT, die Modelle bleiben so direkt vergleichbar. Die
Staffing-Empfehlungen schreibt standardmäßig nur der futureEXPERT-Lauf
(`ML_WRITE_STAFFING=1` überschreibt sie mit Version 2).

## Absicherung

Plausibilitätsprüfung der Prognose gegen die Historie, Untergrenze 0 Besucher,
Mindest-Historie von 60 Tagen, Aktualitätswarnung bei veralteten Daten,
Quantil-Crossing-Korrektur der Intervalle, DB-Verbindungs-Fallback (DS→ETL)
und Kennzeichnung der Wetter-Datenherkunft (`source`-Spalte) je Prognosetag.
