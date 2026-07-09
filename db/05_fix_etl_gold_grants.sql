-- =============================================================================
-- 05_fix_etl_gold_grants.sql
-- Nachtraeglicher Fix: etl_user fehlten die Schreibrechte auf das gold-Schema.
--
-- Symptom im Nacht-Cron:
--   psycopg2.errors.InsufficientPrivilege: permission denied for table feature_store
--
-- Ursache: Die ETL-Pipeline baut den Gold-Feature-Store
-- (etl.transformers.gold_features -> gold.feature_store) und laeuft ueber
-- DATABASE_URL_ETL (= etl_user), hatte in gold aber nur Sequence-, keine
-- Tabellenrechte. create_roles_and_schemas.sql ist bereits korrigiert; dieses
-- Skript bringt die BESTEHENDE NeonDB einmalig auf denselben Stand.
--
-- Ausfuehren als Admin/Owner der DB (z. B. neondb_owner) im Neon-SQL-Editor
-- oder via psql. Idempotent – mehrfaches Ausfuehren schadet nicht.
-- =============================================================================

GRANT USAGE ON SCHEMA gold TO etl_user;

-- Bestehende gold-Tabellen
GRANT INSERT, UPDATE, SELECT ON ALL TABLES IN SCHEMA gold TO etl_user;

-- Kuenftig in gold angelegte Tabellen automatisch mit abdecken
ALTER DEFAULT PRIVILEGES IN SCHEMA gold
    GRANT INSERT, UPDATE, SELECT ON TABLES TO etl_user;

-- Sequenzen (fuer SERIAL/BIGSERIAL-Spalten), damit INSERTs die id vergeben koennen
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA gold TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold
    GRANT USAGE, SELECT ON SEQUENCES TO etl_user;
