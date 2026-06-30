"""
etl/transformers/gold_features.py
Gold-Layer-Aufbau (Medallion-Architektur).

Verknüpft die Roh-/Processed-Schichten zu einem stündlichen Feature-Store:
    raw.library_visitors  (Besucher je Stunde)
  + raw.weather           (Wetter je Stunde)
  + processed.holidays    (Feiertage / Ferien je Tag)
  → gold.feature_store    (ein Datensatz je Öffnungsstunde, join-fertig fürs Modell)

Idempotent: nutzt ON CONFLICT (timestamp_local) DO UPDATE, kann also beliebig
oft laufen, ohne Duplikate zu erzeugen. Aufruf als Teil der ETL-Pipeline
(siehe etl/pipeline.py) oder standalone:

    python -m etl.transformers.gold_features
"""

from __future__ import annotations

import logging

from sqlalchemy import text

from etl.db import engine

logger = logging.getLogger(__name__)


# Eine einzige Mengen-Operation in SQL ist hier deutlich effizienter und
# konsistenter als ein Round-Trip je Zeile. Wochentag/Wochenende/Stunde werden
# in der Zeitzone Europe/Berlin abgeleitet, damit sie zur Öffnungszeit passen.
_BUILD_SQL = """
INSERT INTO gold.feature_store (
    timestamp_local, date_local, hour_local, weekday, is_weekend,
    is_public_holiday, is_school_holiday,
    temperature_c, precipitation_mm, weather_code,
    library_visitor_count
)
SELECT
    v.timestamp_local,
    (v.timestamp_local AT TIME ZONE 'Europe/Berlin')::date                       AS date_local,
    EXTRACT(HOUR  FROM v.timestamp_local AT TIME ZONE 'Europe/Berlin')::smallint  AS hour_local,
    EXTRACT(ISODOW FROM v.timestamp_local AT TIME ZONE 'Europe/Berlin')::smallint AS weekday,
    EXTRACT(ISODOW FROM v.timestamp_local AT TIME ZONE 'Europe/Berlin') IN (6, 7) AS is_weekend,
    COALESCE(h.is_public_holiday, FALSE)                                          AS is_public_holiday,
    COALESCE(h.is_school_holiday, FALSE)                                          AS is_school_holiday,
    w.temperature_c,
    w.precipitation_mm,
    w.weather_code,
    v.count_enter
FROM raw.library_visitors v
LEFT JOIN raw.weather       w ON w.timestamp_local = v.timestamp_local
LEFT JOIN processed.holidays h
       ON h.date_local = (v.timestamp_local AT TIME ZONE 'Europe/Berlin')::date
ON CONFLICT (timestamp_local) DO UPDATE SET
    date_local            = EXCLUDED.date_local,
    hour_local            = EXCLUDED.hour_local,
    weekday               = EXCLUDED.weekday,
    is_weekend            = EXCLUDED.is_weekend,
    is_public_holiday     = EXCLUDED.is_public_holiday,
    is_school_holiday     = EXCLUDED.is_school_holiday,
    temperature_c         = EXCLUDED.temperature_c,
    precipitation_mm      = EXCLUDED.precipitation_mm,
    weather_code          = EXCLUDED.weather_code,
    library_visitor_count = EXCLUDED.library_visitor_count;
"""


def build_feature_store() -> int:
    """
    Baut/aktualisiert gold.feature_store aus den Roh-/Processed-Tabellen.

    Returns:
        Anzahl der Zeilen, die danach im Feature-Store liegen.
    """
    with engine.begin() as conn:
        conn.execute(text(_BUILD_SQL))
        n = conn.execute(text("SELECT count(*) FROM gold.feature_store")).scalar_one()
    logger.info("gold.feature_store aktualisiert – %s Zeilen", n)
    print(f"Feature-Store: {n} Zeilen")
    return int(n)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_feature_store()
