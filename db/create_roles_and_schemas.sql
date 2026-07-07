-- =============================================================================
-- 01_db_setup_roles_schemas.sql
-- Staffing Project – NeonDB Initialisierung
-- Ausführen als: admin / Neon-Root-User
-- Reihenfolge: 1. Rollen, 2. Schemas, 3. Berechtigungen
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. ROLLEN ANLEGEN
-- -----------------------------------------------------------------------------

-- ETL-Bot: schreibt Rohdaten und verarbeitete Daten
CREATE ROLE etl_user WITH LOGIN PASSWORD 'CHANGE_ME_etl_strong_pw';

-- Data Scientist: liest alles, schreibt ins Gold-Schema
CREATE ROLE ds_user WITH LOGIN PASSWORD 'CHANGE_ME_ds_strong_pw';

-- Read-Only: Dashboard, Dokumentation, PM
CREATE ROLE readonly_user WITH LOGIN PASSWORD 'CHANGE_ME_ro_strong_pw';

-- CI/CD: GitHub Actions, führt nur Migrationen aus
CREATE ROLE ci_user WITH LOGIN PASSWORD 'CHANGE_ME_ci_strong_pw';

-- Hinweis: Der Neon-Admin-User (root) ist bereits vorhanden.
-- Credentials NUR im Team-Passwortmanager (z.B. Bitwarden) speichern.
-- NIEMALS in .env committen, NIEMALS im Repository.


-- -----------------------------------------------------------------------------
-- 2. SCHEMAS (Medallion-Architektur)
-- -----------------------------------------------------------------------------

-- RAW: Rohdaten, unveränderlich, exakt wie von der API geliefert
CREATE SCHEMA IF NOT EXISTS raw;

-- PROCESSED: Bereinigt, vereinheitlicht, join-fähig
CREATE SCHEMA IF NOT EXISTS processed;

-- GOLD: ML-Features, Vorhersagen, Staffing-Empfehlungen
CREATE SCHEMA IF NOT EXISTS gold;

-- MONITORING: Pipeline-Logs, Datenqualitätschecks
CREATE SCHEMA IF NOT EXISTS monitoring;


-- -----------------------------------------------------------------------------
-- 3. BERECHTIGUNGEN AUF SCHEMAS
-- -----------------------------------------------------------------------------

-- ETL: Schreibzugriff auf raw + processed + gold
-- Hinweis: Die ETL-Pipeline baut auch den Gold-Feature-Store
-- (etl.transformers.gold_features -> gold.feature_store) und laeuft ueber
-- DATABASE_URL_ETL (= etl_user). Ohne Gold-Schreibrechte scheitert der Lauf mit
-- "permission denied for table feature_store". Daher braucht etl_user auch in
-- gold INSERT/UPDATE/SELECT.
GRANT USAGE ON SCHEMA raw       TO etl_user;
GRANT USAGE ON SCHEMA processed TO etl_user;
GRANT USAGE ON SCHEMA gold      TO etl_user;
GRANT CREATE ON SCHEMA raw       TO etl_user;
GRANT CREATE ON SCHEMA processed TO etl_user;
GRANT INSERT, UPDATE, SELECT ON ALL TABLES IN SCHEMA raw       TO etl_user;
GRANT INSERT, UPDATE, SELECT ON ALL TABLES IN SCHEMA processed TO etl_user;
GRANT INSERT, UPDATE, SELECT ON ALL TABLES IN SCHEMA gold      TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw       GRANT INSERT, UPDATE, SELECT ON TABLES TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA processed GRANT INSERT, UPDATE, SELECT ON TABLES TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold      GRANT INSERT, UPDATE, SELECT ON TABLES TO etl_user;

-- DS: Lesen überall, Schreiben in gold
GRANT USAGE ON SCHEMA raw, processed, gold TO ds_user;
GRANT SELECT ON ALL TABLES IN SCHEMA raw       TO ds_user;
GRANT SELECT ON ALL TABLES IN SCHEMA processed TO ds_user;
GRANT CREATE ON SCHEMA gold TO ds_user;
GRANT INSERT, UPDATE, DELETE, SELECT ON ALL TABLES IN SCHEMA gold TO ds_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw       GRANT SELECT ON TABLES TO ds_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA processed GRANT SELECT ON TABLES TO ds_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold      GRANT INSERT, UPDATE, DELETE, SELECT ON TABLES TO ds_user;

-- READONLY: Lesen auf processed + gold (für Dashboard & Co.)
GRANT USAGE ON SCHEMA processed, gold TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA processed TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA gold      TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA processed GRANT SELECT ON TABLES TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold      GRANT SELECT ON TABLES TO readonly_user;

-- CI: Nur Migrationen (DDL via admin-User – ci_user braucht Schema-Usage)
GRANT USAGE ON SCHEMA raw, processed, gold, monitoring TO ci_user;

-- MONITORING: etl_user darf Logs schreiben
GRANT USAGE ON SCHEMA monitoring TO etl_user;
GRANT CREATE ON SCHEMA monitoring TO etl_user;
GRANT INSERT, SELECT ON ALL TABLES IN SCHEMA monitoring TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA monitoring GRANT INSERT, SELECT ON TABLES TO etl_user;

-- Readonly darf Monitoring-Logs lesen (für Qualitätschecks im Dashboard)
GRANT USAGE ON SCHEMA monitoring TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA monitoring TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA monitoring GRANT SELECT ON TABLES TO readonly_user;