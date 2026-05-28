# ETL

Lädt Daten aus Open-Data-Quellen und schreibt sie in die NeonDB.

---

## Ausführen

```bash
python -m etl.pipeline
```

---

## Quellen

| Quelle | Datei | Tabelle |
|---|---|---|
| Stadtteilbücherei Hubland | `sources/library.py` | `raw.library_visitors` |
| Open-Meteo Wetter | `sources/weather.py` | `raw.weather` |
| Feiertage & Schulferien Bayern | `sources/holidays.py` | `processed.holidays` |

---

## Struktur

```
etl/
├── sources/        # API-Abfragen, gibt DataFrame zurück
├── transformers/   # Bereinigung (für Nico/Feature Engineering)
├── loaders/        # UPSERT in NeonDB
├── config.py       # Lädt .env
├── db.py           # DB-Verbindung
└── pipeline.py     # Führt alle Sources nacheinander aus
```

---

## Neue Quelle hinzufügen

1. `sources/<name>.py` mit `fetch_all()` Funktion erstellen
2. `loaders/postgres.py` um `load_<name>()` ergänzen
3. In `pipeline.py` einbinden