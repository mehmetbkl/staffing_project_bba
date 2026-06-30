-- =============================================================================
-- 03_staff_schema.sql
-- Staffing Project – Personalstammdaten in der DB
-- Ausführen als: admin-User
-- Reihenfolge: NACH 02_create_tables.sql
--
-- Verlagert die bislang hartcodierten Mitarbeiter-/Schichtdaten
-- (dashboard/data/employees.py) in die Datenbank, damit Backend, Dashboard und
-- spätere Planungslogik konsistent auf eine Quelle zugreifen.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS staff;

-- Mitarbeiterstammdaten
CREATE TABLE IF NOT EXISTS staff.employees (
    id          TEXT PRIMARY KEY,            -- Kürzel, z. B. 'AK'
    name        TEXT NOT NULL,
    role        TEXT NOT NULL,               -- 'Kassierer' | 'Abteilungsleiter' | 'Lagerist'
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Wöchentlicher Schichtplan (eine Zeile je Mitarbeiter & Wochentag mit Dienst)
CREATE TABLE IF NOT EXISTS staff.shifts (
    id           BIGSERIAL PRIMARY KEY,
    employee_id  TEXT NOT NULL REFERENCES staff.employees(id) ON DELETE CASCADE,
    weekday      SMALLINT NOT NULL CHECK (weekday BETWEEN 1 AND 7),  -- 1=Mo .. 7=So
    shift_start  TIME NOT NULL,
    shift_end    TIME NOT NULL,
    UNIQUE (employee_id, weekday)
);

CREATE INDEX IF NOT EXISTS idx_shifts_weekday ON staff.shifts (weekday);

-- -----------------------------------------------------------------------------
-- Berechtigungen
-- -----------------------------------------------------------------------------
-- readonly_user (Dashboard) liest die Personaldaten.
GRANT USAGE  ON SCHEMA staff TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA staff TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA staff GRANT SELECT ON TABLES TO readonly_user;

-- etl_user/ds_user dürfen die Stammdaten pflegen.
GRANT USAGE ON SCHEMA staff TO etl_user, ds_user;
GRANT INSERT, UPDATE, DELETE, SELECT ON ALL TABLES IN SCHEMA staff TO etl_user, ds_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA staff TO etl_user, ds_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA staff
    GRANT INSERT, UPDATE, DELETE, SELECT ON TABLES TO etl_user, ds_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA staff
    GRANT USAGE, SELECT ON SEQUENCES TO etl_user, ds_user;

-- -----------------------------------------------------------------------------
-- Stammdaten (Migration aus dashboard/data/employees.py)
-- -----------------------------------------------------------------------------
INSERT INTO staff.employees (id, name, role) VALUES
    ('AK', 'Anna K.',   'Kassierer'),
    ('TM', 'Thomas M.', 'Abteilungsleiter'),
    ('SB', 'Sara B.',   'Kassierer'),
    ('MR', 'Max R.',    'Lagerist'),
    ('LW', 'Lisa W.',   'Kassierer'),
    ('KS', 'Klaus S.',  'Abteilungsleiter')
ON CONFLICT (id) DO NOTHING;

-- weekday: 1=Mo 2=Di 3=Mi 4=Do 5=Fr 6=Sa 7=So
INSERT INTO staff.shifts (employee_id, weekday, shift_start, shift_end) VALUES
    -- Anna K.
    ('AK', 1, '08:00', '14:00'), ('AK', 2, '08:00', '14:00'),
    ('AK', 3, '12:00', '20:00'), ('AK', 5, '08:00', '14:00'),
    ('AK', 6, '10:00', '16:00'),
    -- Thomas M.
    ('TM', 1, '08:00', '16:00'), ('TM', 2, '08:00', '16:00'),
    ('TM', 3, '08:00', '16:00'), ('TM', 4, '08:00', '16:00'),
    ('TM', 5, '08:00', '16:00'),
    -- Sara B.
    ('SB', 1, '10:00', '18:00'), ('SB', 3, '10:00', '18:00'),
    ('SB', 4, '10:00', '18:00'), ('SB', 5, '10:00', '18:00'),
    ('SB', 6, '08:00', '14:00'),
    -- Max R.
    ('MR', 1, '06:00', '14:00'), ('MR', 2, '06:00', '14:00'),
    ('MR', 4, '06:00', '14:00'), ('MR', 5, '06:00', '14:00'),
    ('MR', 6, '06:00', '12:00'),
    -- Lisa W.
    ('LW', 2, '14:00', '20:00'), ('LW', 3, '14:00', '20:00'),
    ('LW', 4, '14:00', '20:00'), ('LW', 5, '14:00', '20:00'),
    ('LW', 6, '12:00', '20:00'),
    -- Klaus S.
    ('KS', 3, '12:00', '20:00'), ('KS', 4, '12:00', '20:00'),
    ('KS', 5, '12:00', '20:00'), ('KS', 6, '10:00', '18:00')
ON CONFLICT (employee_id, weekday) DO NOTHING;
