-- =============================================================================
-- 04_gold_build.sql
-- Staffing Project – Gold-Layer befüllen
-- Ausführen als: admin- oder ds_user
-- Reihenfolge: NACH 02_create_tables.sql, sobald raw/processed Daten enthalten
--
-- Baut:
--   1. gold.feature_store              (stündliche Features, join-fertig)
--   2. gold.predictions               (saisonale Baseline-Tagesprognose, 30 Tage)
--   3. gold.staffing_recommendations  (Schicht-Personalempfehlung je Tag)
--
-- Hinweis: Die Schritte 2+3 spiegeln models(Nico)/baseline_forecast.py als
-- reine SQL-Variante, damit die DB auch ohne Python-Lauf befüllt werden kann.
-- Idempotent über ON CONFLICT.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. FEATURE STORE (stündlich)
-- -----------------------------------------------------------------------------
INSERT INTO gold.feature_store (
    timestamp_local, date_local, hour_local, weekday, is_weekend,
    is_public_holiday, is_school_holiday,
    temperature_c, precipitation_mm, weather_code,
    library_visitor_count
)
SELECT
    v.timestamp_local,
    (v.timestamp_local AT TIME ZONE 'Europe/Berlin')::date,
    EXTRACT(HOUR   FROM v.timestamp_local AT TIME ZONE 'Europe/Berlin')::smallint,
    EXTRACT(ISODOW FROM v.timestamp_local AT TIME ZONE 'Europe/Berlin')::smallint,
    EXTRACT(ISODOW FROM v.timestamp_local AT TIME ZONE 'Europe/Berlin') IN (6, 7),
    COALESCE(h.is_public_holiday, FALSE),
    COALESCE(h.is_school_holiday, FALSE),
    w.temperature_c, w.precipitation_mm, w.weather_code,
    v.count_enter
FROM raw.library_visitors v
LEFT JOIN raw.weather        w ON w.timestamp_local = v.timestamp_local
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

-- -----------------------------------------------------------------------------
-- 2. BASELINE-PROGNOSE → gold.predictions  (saisonal: Median je Wochentag)
-- -----------------------------------------------------------------------------
WITH daily AS (
    SELECT date_local,
           SUM(library_visitor_count)  AS visitors,
           MAX(weekday)                AS weekday
    FROM gold.feature_store
    GROUP BY date_local
),
profile AS (   -- robustes Saisonprofil je Wochentag
    SELECT weekday,
           percentile_cont(0.5)  WITHIN GROUP (ORDER BY visitors) AS med,
           percentile_cont(0.25) WITHIN GROUP (ORDER BY visitors) AS q1,
           percentile_cont(0.75) WITHIN GROUP (ORDER BY visitors) AS q3
    FROM daily
    GROUP BY weekday
),
horizon AS (   -- nächste 30 Tage ab morgen
    SELECT (CURRENT_DATE + g)::date AS d,
           EXTRACT(ISODOW FROM (CURRENT_DATE + g))::smallint AS weekday
    FROM generate_series(1, 30) AS g
)
INSERT INTO gold.predictions
    (model_name, model_version, timestamp_local,
     predicted_visitors, confidence_lower, confidence_upper)
SELECT 'baseline', 'seasonal-naive-v1',
       (h.d::timestamp AT TIME ZONE 'Europe/Berlin'),
       ROUND(p.med),
       ROUND(GREATEST(p.q1, 0)),
       ROUND(p.q3)
FROM horizon h
JOIN profile p ON p.weekday = h.weekday
ON CONFLICT (model_name, model_version, timestamp_local) DO UPDATE SET
    predicted_visitors = EXCLUDED.predicted_visitors,
    confidence_lower   = EXCLUDED.confidence_lower,
    confidence_upper   = EXCLUDED.confidence_upper,
    predicted_at       = NOW();

-- -----------------------------------------------------------------------------
-- 3. PERSONALEMPFEHLUNG → gold.staffing_recommendations
--    Tagesprognose über Öffnungsprofil auf 3 Schichten verteilt; je Schicht
--    wird die Spitzenstunde bewertet (Schwellenwerte wie im Dashboard).
-- -----------------------------------------------------------------------------
WITH shape(h, w) AS (   -- Tagesform 8..21 Uhr (identisch zum Dashboard)
    VALUES (8,15),(9,25),(10,45),(11,75),(12,90),(13,85),(14,100),
           (15,110),(16,95),(17,80),(18,70),(19,60),(20,45),(21,30)
),
shape_sum AS (SELECT SUM(w)::numeric AS s FROM shape),
pred AS (
    SELECT timestamp_local::date AS d, predicted_visitors AS total
    FROM gold.predictions
    WHERE model_name = 'baseline' AND model_version = 'seasonal-naive-v1'
      AND timestamp_local::date >= CURRENT_DATE
),
hourly AS (
    SELECT p.d, s.h, (p.total * s.w / ss.s) AS visitors_h
    FROM pred p CROSS JOIN shape s CROSS JOIN shape_sum ss
),
shifts(name, h_start, h_end) AS (
    VALUES ('Früh', 8, 13), ('Mittag', 13, 17), ('Spät', 17, 21)
),
per_shift AS (
    SELECT hr.d, sh.name, sh.h_start, sh.h_end,
           MAX(hr.visitors_h) AS peak,
           SUM(hr.visitors_h) AS total
    FROM hourly hr
    JOIN shifts sh ON hr.h >= sh.h_start AND hr.h < sh.h_end
    GROUP BY hr.d, sh.name, sh.h_start, sh.h_end
)
INSERT INTO gold.staffing_recommendations
    (date_local, shift, shift_start, shift_end,
     predicted_visitors, recommended_staff, demand_level, model_version)
SELECT d, name,
       make_time(h_start, 0, 0), make_time(h_end, 0, 0),
       ROUND(total)::int,
       CASE
         WHEN peak >= 200 THEN 7 WHEN peak >= 160 THEN 6
         WHEN peak >= 120 THEN 5 WHEN peak >=  80 THEN 4
         WHEN peak >=  50 THEN 3 WHEN peak >=  20 THEN 2
         ELSE 1
       END,
       CASE WHEN peak >= 120 THEN 'hoch'
            WHEN peak >=  50 THEN 'mittel'
            ELSE 'niedrig' END,
       'seasonal-naive-v1'
FROM per_shift
ON CONFLICT (date_local, shift) DO UPDATE SET
    shift_start        = EXCLUDED.shift_start,
    shift_end          = EXCLUDED.shift_end,
    predicted_visitors = EXCLUDED.predicted_visitors,
    recommended_staff  = EXCLUDED.recommended_staff,
    demand_level       = EXCLUDED.demand_level,
    model_version      = EXCLUDED.model_version,
    created_at         = NOW();
