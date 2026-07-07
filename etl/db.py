import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Robuste Engine-Konfiguration für NeonDB (Serverless, scale-to-zero):
# - connect_timeout: haengt der Verbindungsaufbau (z. B. weil die Neon-Compute
#   erst aus dem Ruhezustand aufwacht oder nicht erreichbar ist), bricht psycopg2
#   nach 15 s ab, statt unbegrenzt zu warten (Ursache frueherer 15-Min-Timeouts).
# - options=statement_timeout: eine einzelne haengende Query wird serverseitig
#   nach 120 s abgebrochen, statt den ganzen Job blockieren zu lassen.
# - pool_pre_ping: tote/geschlossene Verbindungen werden vor Nutzung erkannt.
# - keepalives: haelt die Verbindung waehrend laengerer Batch-Inserts am Leben.
_DB_URL = os.environ.get("DATABASE_URL_ETL")

engine = create_engine(
    _DB_URL,
    pool_pre_ping=True,
    # Echtes Batching auf psycopg2-Ebene: fasst viele INSERT-Zeilen zu wenigen
    # Netzwerk-Round-Trips zusammen (statt 1 Round-Trip je Zeile). Ohne das
    # sendet SQLAlchemy trotz Parameterliste je Zeile einzeln -> bei >10.000
    # Wetterzeilen sehr langsam.
    executemany_mode="values_plus_batch",
    connect_args={
        "connect_timeout": 15,
        "options": "-c statement_timeout=120000",  # 120 s je Statement
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)


def test_connection():
    with engine.connect() as conn:
        row = conn.execute(text("SELECT current_user, current_database()")).fetchone()
        print(f"User: {row[0]} | DB: {row[1]}")


if __name__ == "__main__":
    test_connection()
