"""
services/db.py
Zentrale DB-Anbindung für das Dashboard.

Liest die NeonDB über DATABASE_URL_ETL (aus der .env im Projekt-Root).
Alle Zugriffe sind „graceful": Ist keine Verbindung möglich oder eine
Abfrage leer, liefern die aufrufenden Services Demo-Daten zurück – das
Dashboard läuft dann weiter, nur eben im Demo-Modus.

Verwendung:
    from services.db import get_engine, db_available, read_sql

    df = read_sql("SELECT ... ")   # gibt None zurück, wenn DB nicht da ist
"""

from __future__ import annotations
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# .env liegt im Projekt-Root (eine Ebene über /dashboard)
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def _load_env() -> None:
    """Lädt die .env aus dem Projekt-Root, ohne harte Abhängigkeit."""
    try:
        from dotenv import load_dotenv
        if _ENV_PATH.exists():
            load_dotenv(_ENV_PATH)
            logger.info("DB: .env geladen aus %s", _ENV_PATH)
        else:
            load_dotenv()  # Fallback: Standard-Suche
    except Exception as exc:
        logger.warning("DB: python-dotenv nicht verfügbar (%s)", exc)


@lru_cache(maxsize=1)
def get_engine():
    """
    Erzeugt einmalig eine SQLAlchemy-Engine aus DATABASE_URL_ETL.
    Gibt None zurück, wenn keine URL gesetzt ist oder SQLAlchemy fehlt.
    Die Verbindung selbst wird erst beim ersten Query aufgebaut (lazy).
    """
    _load_env()
    url = os.environ.get("DATABASE_URL_ETL")
    if not url:
        logger.info("DB: DATABASE_URL_ETL nicht gesetzt – Demo-Modus.")
        return None
    try:
        from sqlalchemy import create_engine
        # pool_pre_ping fängt abgebrochene Verbindungen ab
        engine = create_engine(url, pool_pre_ping=True, pool_recycle=300)
        return engine
    except Exception as exc:
        logger.warning("DB: Engine konnte nicht erstellt werden: %s", exc)
        return None


@lru_cache(maxsize=1)
def db_available() -> bool:
    """
    Prüft EINMALIG, ob die DB erreichbar ist (kurzer SELECT 1).
    Ergebnis wird gecacht, damit nicht jede Seite neu verbindet.
    """
    engine = get_engine()
    if engine is None:
        return False
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("DB: Verbindung OK – Live-Modus.")
        return True
    except Exception as exc:
        logger.info("DB: nicht erreichbar (%s) – Demo-Modus.", str(exc)[:120])
        return False


def read_sql(query: str, params: Optional[dict] = None):
    """
    Führt eine SELECT-Abfrage aus und gibt einen DataFrame zurück.
    Bei jedem Problem (keine DB, Fehler) → None, damit der Aufrufer
    sauber auf Demo-Daten zurückfallen kann.
    """
    if not db_available():
        return None
    try:
        import pandas as pd
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params or {})
    except Exception as exc:
        logger.warning("DB: Abfrage fehlgeschlagen: %s", str(exc)[:160])
        return None


def reset_cache() -> None:
    """Cache zurücksetzen (z. B. nach .env-Änderung im laufenden Betrieb)."""
    db_available.cache_clear()
    get_engine.cache_clear()
