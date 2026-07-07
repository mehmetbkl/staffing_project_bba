import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text

load_dotenv()

# Robuste Engine-Konfiguration für NeonDB (Serverless, ueber den -pooler-Endpoint):
# - connect_timeout: bricht einen haengenden Verbindungsaufbau nach 15 s ab,
#   statt unbegrenzt zu warten.
# - pool_pre_ping: tote/geschlossene Verbindungen werden vor Nutzung erkannt.
# - keepalives: haelt die Verbindung waehrend laengerer Batch-Inserts am Leben.
# - executemany_mode: echtes Batching auf psycopg2-Ebene -> viele INSERT-Zeilen
#   in wenigen Netzwerk-Round-Trips statt einem je Zeile (bei >10.000 Wetterzeilen
#   entscheidend fuer die Laufzeit).
#
# WICHTIG (Neon-Pooler): statement_timeout darf NICHT ueber das libpq-"options"-
# Startup-Paket gesetzt werden – der Neon-Pooler lehnt das ab
# ("unsupported startup parameter in options"). Stattdessen wird es unten per
# 'SET statement_timeout' nach jedem Connect gesetzt (das erlaubt der Pooler).
_DB_URL = os.environ.get("DATABASE_URL_ETL")

# 120 s je Statement; 0 = aus.
STATEMENT_TIMEOUT_MS = 120_000

engine = create_engine(
    _DB_URL,
    pool_pre_ping=True,
    executemany_mode="values_plus_batch",
    connect_args={
        "connect_timeout": 15,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)


@event.listens_for(engine, "connect")
def _set_statement_timeout(dbapi_connection, _connection_record):
    """Setzt statement_timeout pro Verbindung – pooler-kompatibel (SET-Befehl)."""
    with dbapi_connection.cursor() as cur:
        cur.execute(f"SET statement_timeout = {STATEMENT_TIMEOUT_MS}")


def test_connection():
    with engine.connect() as conn:
        row = conn.execute(text("SELECT current_user, current_database()")).fetchone()
        print(f"User: {row[0]} | DB: {row[1]}")


if __name__ == "__main__":
    test_connection()
