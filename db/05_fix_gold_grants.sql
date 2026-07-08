-- =============================================================================
-- 05_fix_gold_grants.sql
-- Behebt ZWEI Rechte-Lücken im Gold-Schema (Fehler aus der Praxis):
--
--   1) ds_user hat INSERT/UPDATE auf die gold-Tabellen, aber keine Rechte
--      auf deren id-Sequenzen:
--        -> "permission denied for sequence predictions_id_seq"
--        (models(Nico)/futureexpert_forecast.py & ml_forecast.py, DB-Write)
--
--   2) etl_user baut in etl/pipeline.py den gold.feature_store, hat laut
--      create_roles_and_schemas.sql aber keinerlei gold-Rechte:
--        -> "permission denied for table feature_store"
--        (python -m etl.pipeline, letzter Schritt)
--
-- EINMALIG als Admin ausführen (Standard-Rolle neondb_owner):
-- Neon Console (console.neon.tech) -> Projekt -> SQL Editor -> einfügen -> Run
-- =============================================================================

-- 1) ds_user: Sequenz-Rechte für Prognose-Writes
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA gold TO ds_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold GRANT USAGE, SELECT ON SEQUENCES TO ds_user;

-- 2) etl_user: Feature-Store-Build (bewusst nur diese eine Tabelle,
--    Prognose-Tabellen bleiben ds_user vorbehalten)
GRANT USAGE ON SCHEMA gold TO etl_user;
GRANT INSERT, UPDATE, SELECT ON gold.feature_store TO etl_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA gold TO etl_user;

-- Kontrolle (alle Zeilen sollten true liefern):
SELECT sequencename,
       has_sequence_privilege('ds_user',  schemaname || '.' || sequencename, 'USAGE') AS ds_ok,
       has_sequence_privilege('etl_user', schemaname || '.' || sequencename, 'USAGE') AS etl_ok
FROM pg_sequences
WHERE schemaname = 'gold';

SELECT has_table_privilege('etl_user', 'gold.feature_store', 'INSERT') AS etl_feature_store_ok,
       has_table_privilege('ds_user',  'gold.predictions',   'INSERT') AS ds_predictions_ok;
