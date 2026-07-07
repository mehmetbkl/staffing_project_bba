"""
etl/diagnose.py
Standalone-Diagnose fuer den ETL-Timeout.

Fuehrt jeden potenziell haengenden Schritt EINZELN mit Zeitmessung aus und
gibt sofort (unbuffered) aus, wo es klemmt. Anders als die volle Pipeline
schreibt dieses Skript NICHTS in die DB ausser einer harmlosen SELECT-Probe.

Aufruf (lokal, mit gesetzter .env / DATABASE_URL_ETL):
    python -m etl.diagnose

Erwartete Ausgabe: jede Zeile mit Dauer. Bleibt es an einer Stelle stehen,
ist genau das der Flaschenhals (typisch: 'DB: connect' bei schlafender NeonDB).
"""

import os
import sys
import time

# .env frueh laden, damit DATABASE_URL_ETL schon vor dem ersten Check verfuegbar
# ist (sonst zeigt die Diagnose faelschlich 'gesetzt: False').
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _timed(name: str, fn):
    _log(f"START  {name}")
    t0 = time.time()
    try:
        out = fn()
        _log(f"OK     {name}  ({time.time() - t0:.1f}s)")
        return out
    except Exception as e:
        _log(f"FEHLER {name}  ({time.time() - t0:.1f}s): {type(e).__name__}: {e}")
        raise


def main() -> None:
    _log("=== ETL-Diagnose gestartet ===")
    url = os.environ.get("DATABASE_URL_ETL")
    _log(f"DATABASE_URL_ETL gesetzt: {bool(url)}")

    # 1) DB-Verbindung (haeufigster Haenger: schlafende NeonDB ohne Timeout)
    from etl.db import engine
    from sqlalchemy import text

    def _connect_probe():
        with engine.connect() as conn:
            return conn.execute(text("SELECT 1")).scalar_one()

    _timed("DB: connect + SELECT 1", _connect_probe)

    # 2) Zeilenzahlen der Zieltabellen (zeigt, ob schon Daten drin sind)
    def _counts():
        with engine.connect() as conn:
            for tbl in ("raw.library_visitors", "raw.weather",
                        "processed.holidays", "gold.feature_store"):
                try:
                    n = conn.execute(text(f"SELECT count(*) FROM {tbl}")).scalar_one()
                    _log(f"    {tbl}: {n} Zeilen")
                except Exception as e:
                    _log(f"    {tbl}: FEHLER {type(e).__name__}: {e}")
    _timed("DB: Tabellen zaehlen", _counts)

    # 3) Quellen einzeln holen (kein DB-Schreiben)
    from etl.sources.library import fetch_all as fetch_library
    from etl.sources.weather import fetch_all as fetch_weather
    from etl.sources.holidays import fetch_all as fetch_holidays

    lib = _timed("Quelle: Library holen", fetch_library)
    _log(f"    Library-Zeilen: {len(lib)}")
    wx = _timed("Quelle: Weather holen", fetch_weather)
    _log(f"    Weather-Zeilen: {len(wx)}")
    hol = _timed("Quelle: Holidays holen", fetch_holidays)
    _log(f"    Holidays-Zeilen: {len(hol)}")

    # 4) INSERT-Test (idempotent, ON CONFLICT DO NOTHING -> kein Datenschaden):
    #    schreibt die geholten Zeilen und misst die Zeit. Das ist der eigentliche
    #    Flaschenhals-Test – mit executemany_mode sollte das Sekunden statt
    #    Minuten dauern. Ueberspringbar mit  --no-write.
    if "--no-write" in sys.argv:
        _log("INSERT-Test uebersprungen (--no-write)")
    else:
        from etl.loaders.postgres import load_library, load_weather, load_holidays
        _timed(f"INSERT: Library ({len(lib)} Zeilen)", lambda: load_library(lib))
        _timed(f"INSERT: Weather ({len(wx)} Zeilen)", lambda: load_weather(wx))
        _timed(f"INSERT: Holidays ({len(hol)} Zeilen)", lambda: load_holidays(hol))

    _log("=== Diagnose fertig – kein Haenger gefunden ===")


if __name__ == "__main__":
    main()
