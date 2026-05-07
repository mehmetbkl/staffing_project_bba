-- =============================================================================
-- 02_create_tables.sql
-- Staffing Project – Tabellendefinitionen
-- Ausführen als: admin-User
-- Reihenfolge: NACH 01_db_setup_roles_schemas.sql
-- =============================================================================


-- =============================================================================
-- SCHEMA: raw
-- =============================================================================

CREATE TABLE IF NOT EXISTS raw.library_visitors (
    id              BIGSERIAL PRIMARY KEY,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    timestamp_local TIMESTAMPTZ NOT NULL UNIQUE,
    count_enter     INTEGER,
    count_exit      INTEGER
);

CREATE TABLE IF NOT EXISTS raw.weather (
    id               BIGSERIAL PRIMARY KEY,
    fetched_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    timestamp_local  TIMESTAMPTZ NOT NULL UNIQUE,
    temperature_c    NUMERIC(5,2),
    precipitation_mm NUMERIC(6,2),
    weather_code     SMALLINT,
    wind_speed_kmh   NUMERIC(6,2),
    cloud_cover_pct  SMALLINT
);


-- =============================================================================
-- SCHEMA: processed
-- =============================================================================

CREATE TABLE IF NOT EXISTS processed.holidays (
    id                BIGSERIAL PRIMARY KEY,
    date_local        DATE NOT NULL UNIQUE,
    is_public_holiday BOOLEAN NOT NULL,
    is_school_holiday BOOLEAN NOT NULL,
    holiday_name      TEXT
);


-- =============================================================================
-- SCHEMA: gold
-- =============================================================================

CREATE TABLE IF NOT EXISTS gold.feature_store (
    id                BIGSERIAL PRIMARY KEY,
    timestamp_local   TIMESTAMPTZ NOT NULL UNIQUE,
    date_local        DATE NOT NULL,
    hour_local        SMALLINT NOT NULL,
    weekday           SMALLINT NOT NULL,
    is_weekend        BOOLEAN NOT NULL,
    is_public_holiday BOOLEAN NOT NULL,
    is_school_holiday BOOLEAN NOT NULL,
    temperature_c     NUMERIC(5,2),
    precipitation_mm  NUMERIC(6,2),
    weather_code      SMALLINT,
    count_enter       INTEGER,
    count_exit        INTEGER,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gold.predictions (
    id                 BIGSERIAL PRIMARY KEY,
    model_name         TEXT NOT NULL,
    model_version      TEXT NOT NULL,
    predicted_at       TIMESTAMPTZ DEFAULT NOW(),
    timestamp_local    TIMESTAMPTZ NOT NULL,
    predicted_visitors NUMERIC(8,2),
    confidence_lower   NUMERIC(8,2),
    confidence_upper   NUMERIC(8,2),
    UNIQUE (model_name, model_version, timestamp_local)
);

CREATE TABLE IF NOT EXISTS gold.staffing_recommendations (
    id                 BIGSERIAL PRIMARY KEY,
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    date_local         DATE NOT NULL,
    shift              TEXT NOT NULL,
    shift_start        TIME NOT NULL,
    shift_end          TIME NOT NULL,
    predicted_visitors INTEGER,
    recommended_staff  SMALLINT NOT NULL,
    demand_level       TEXT,
    model_version      TEXT,
    UNIQUE (date_local, shift)
);


-- =============================================================================
-- GRANTS
-- =============================================================================

GRANT USAGE, SELECT ON SEQUENCE raw.library_visitors_id_seq          TO etl_user;
GRANT USAGE, SELECT ON SEQUENCE raw.weather_id_seq                   TO etl_user;
GRANT USAGE, SELECT ON SEQUENCE processed.holidays_id_seq            TO etl_user;
GRANT USAGE, SELECT ON SEQUENCE gold.feature_store_id_seq            TO etl_user;
GRANT USAGE, SELECT ON SEQUENCE gold.predictions_id_seq              TO etl_user;
GRANT USAGE, SELECT ON SEQUENCE gold.staffing_recommendations_id_seq TO etl_user;