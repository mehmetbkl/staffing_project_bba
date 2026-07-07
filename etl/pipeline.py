"""
etl/pipeline.py
Voller ETL-Lauf: Rohdaten holen + laden (Library, Wetter, Holidays) und den
Gold-Feature-Store bauen.

Diagnose: Jeder Schritt wird mit Dauer geloggt und die Ausgabe wird sofort
geflusht (unbuffered), damit im GitHub-Actions-Log sichtbar ist, wo Zeit
verbraucht wird bzw. wo es haengt (frueher lief der Schritt 15 Min ohne jede
Ausgabe ins Timeout).
"""

import sys
import time

from etl.sources.library import fetch_all as fetch_library
from etl.sources.weather import fetch_all as fetch_weather
from etl.sources.holidays import fetch_all as fetch_holidays
from etl.loaders.postgres import load_library, load_weather, load_holidays
from etl.transformers.gold_features import build_feature_store


def _log(msg: str) -> None:
    """Zeitgestempelte, sofort geflushte Log-Zeile."""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _step(name: str, fn):
    """Fuehrt einen Pipeline-Schritt aus und loggt Start/Ende + Dauer."""
    _log(f"START  {name}")
    t0 = time.time()
    result = fn()
    _log(f"DONE   {name}  ({time.time() - t0:.1f}s)")
    return result


def run():
    _log("Pipeline-Lauf gestartet")

    lib = _step("Library: fetch", fetch_library)
    _step(f"Library: load ({len(lib)} Zeilen)", lambda: load_library(lib))

    wx = _step("Weather: fetch", fetch_weather)
    _step(f"Weather: load ({len(wx)} Zeilen)", lambda: load_weather(wx))

    hol = _step("Holidays: fetch", fetch_holidays)
    _step(f"Holidays: load ({len(hol)} Zeilen)", lambda: load_holidays(hol))

    _step("Feature-Store (Gold) bauen", build_feature_store)

    _log("Pipeline done.")


if __name__ == "__main__":
    # Unbuffered stdout/stderr erzwingen (falls PYTHONUNBUFFERED nicht gesetzt ist),
    # damit die Logs live im Actions-Log erscheinen.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    run()
