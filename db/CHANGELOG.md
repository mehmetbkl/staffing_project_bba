# Datenbank-Änderungen (NeonDB `staffing_retail_db`)

Dokumentiert alle Schema- und Datenanpassungen im Rahmen der Finalisierung.
Branch: `production` · Datenbank: `neondb`.

## Ausgangslage (vor Finalisierung)

| Schema.Tabelle | Zeilen | Zeitraum | Status |
|---|---|---|---|
| `raw.library_visitors` | 5.499 | 2025-04-24 – 2025-05-07 | befüllt |
| `raw.weather` | 9.096 | 2025-04-24 – 2025-05-07 | befüllt |
| `processed.holidays` | 379 | 2025-04-24 – 2026-05-07 | befüllt |
| `gold.feature_store` | 0 | – | **leer** |
| `gold.predictions` | 0 | – | **leer** |
| `gold.staffing_recommendations` | 0 | – | **leer** |

Wichtige Abweichung zum committeten `create_tables.sql`: Die Live-Tabelle
`gold.feature_store` enthält zusätzliche Spalten
(`pedestrian_schoenbornstrasse`, `event_count_nearby`, `event_max_visitors`)
und nutzt `library_visitor_count` statt `count_enter`/`count_exit`.
`create_tables.sql` wurde an die Realität angepasst.

## Durchgeführte Änderungen

### 1. Gold-Layer befüllt (`04_gold_build.sql`)

- **`gold.feature_store`**: stündliche Features aus `raw.library_visitors` +
  `raw.weather` + `processed.holidays` (Join über Zeitstempel/Datum, Wochentag &
  Feiertagsflags in Zeitzone Europe/Berlin). Spalte `library_visitor_count`.
- **`gold.predictions`**: 30-Tage-Baseline-Prognose (saisonaler Median je
  Wochentag, Quartile als Konfidenzband). `model_name='baseline'`,
  `model_version='seasonal-naive-v1'`.
- **`gold.staffing_recommendations`**: je Prognosetag 3 Schichten
  (Früh 8–13, Mittag 13–17, Spät 17–21); empfohlene Mitarbeiterzahl aus der
  Spitzenstunde über die Staffing-Schwellenwerte.

### 2. Neues Schema `staff` (`03_staff_schema.sql`)

- `staff.employees` (id, name, role, active, created_at) – 6 Mitarbeiter.
- `staff.shifts` (employee_id FK, weekday 1–7, shift_start, shift_end) – 29 Zeilen.
- Index `idx_shifts_weekday`.
- Daten migriert aus `dashboard/data/employees.py`.

### 3. Berechtigungen

- `etl_user`: `USAGE` + `SELECT` auf Schema `gold` (Dashboard liest die
  Prognose über die ETL-URL).
- `etl_user`, `readonly_user`: `USAGE` + `SELECT` auf Schema `staff`.
- `ds_user`: Schreibrechte auf `staff` (Pflege der Stammdaten).
- Default Privileges entsprechend gesetzt.

## Reproduktion

Skripte in Reihenfolge ausführen (als admin/owner):

```
db/create_roles_and_schemas.sql   # einmalig (Rollen + Schemas)  – bereits vorhanden
db/create_tables.sql              # Tabellen raw/processed/gold
db/03_staff_schema.sql            # staff-Schema + Stammdaten
db/04_gold_build.sql              # Gold-Layer befüllen (nach ETL-Lauf)
```

Alternativ Python: `python -m etl.pipeline` (baut auch `gold.feature_store`),
danach `python "models(Nico)/baseline_forecast.py"` für Prognose + Empfehlungen.

## Offen / Hinweise

- Roh-Daten enden am **2025-05-07**. Für aktuelle Prognosen muss die
  ETL-Pipeline erneut laufen (Open-Meteo + Bibliotheks-Quelle).
- Die Spalten `pedestrian_schoenbornstrasse`, `event_count_nearby`,
  `event_max_visitors` sind Platzhalter ohne ETL-Quelle (bleiben NULL).
