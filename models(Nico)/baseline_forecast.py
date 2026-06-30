"""
models(Nico)/baseline_forecast.py
Reproduzierbare Baseline-Prognose – ohne externen Dienst, ohne ANN.

Zweck
-----
futureexpert_forecast.py liefert die "beste" Prognose über den externen Dienst
futureEXPERT. Dieser Dienst braucht Credentials und Online-Zugang und ist damit
nicht immer lauffähig (CI, Offline, Demo). Diese Baseline schließt die Lücke:
sie berechnet eine saisonale Tagesprognose direkt aus gold.feature_store und
schreibt sie – exakt wie futureEXPERT – nach gold.predictions und
gold.staffing_recommendations.

So hat das Dashboard immer echte Werte (Live-Modus statt Demo), und das Team
hat eine Baseline, gegen die das futureEXPERT-Modell verglichen werden kann
(MAE/RMSE/MAPE – siehe Projektskizze, Phase Modellierung).

Methodik
--------
Tagessumme der Besucher = saisonaler Mittelwert je (Wochentag, Feiertagsflag),
robust über den Median der letzten vollständigen Tage. Das ist die klassische
"seasonal naive"-Baseline und für Personalplanung gut interpretierbar.
Das Konfidenzband ergibt sich aus dem Interquartilsabstand je Wochentag.

Aufruf:
    python -m models_nico.baseline_forecast            # 30 Tage voraus
    (bzw.) python "models(Nico)/baseline_forecast.py"
"""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# forecast_db liegt im selben Ordner
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forecast_db import write_predictions, write_staffing_recommendations  # noqa: E402

logger = logging.getLogger(__name__)

MODEL_NAME = "baseline"
MODEL_VERSION = "seasonal-naive-v1"
HORIZON_DAYS = 30


def _engine():
    load_dotenv()
    url = os.environ.get("DATABASE_URL_DS") or os.environ.get("DATABASE_URL_ETL")
    if not url:
        raise RuntimeError("DATABASE_URL_DS/ETL nicht gesetzt.")
    return create_engine(url)


def _load_daily_history(engine) -> pd.DataFrame:
    """Tages-Besuchersummen + Wochentag/Feiertag aus dem Gold-Feature-Store."""
    df = pd.read_sql(text("""
        SELECT date_local,
               SUM(library_visitor_count)      AS visitors,
               MAX(weekday)                    AS weekday,
               BOOL_OR(is_public_holiday)      AS is_public_holiday
        FROM gold.feature_store
        GROUP BY date_local
        ORDER BY date_local
    """), engine.connect())
    return df


def build_baseline_forecast(engine=None, horizon: int = HORIZON_DAYS) -> pd.DataFrame:
    """
    Berechnet die saisonale Tagesprognose für die nächsten `horizon` Tage.

    Returns DataFrame mit Spalten datum, forecast, low, high (kompatibel zu
    forecast_db.write_predictions).
    """
    engine = engine or _engine()
    hist = _load_daily_history(engine)
    if hist.empty:
        raise RuntimeError(
            "gold.feature_store ist leer – bitte zuerst die ETL-Pipeline / "
            "den Feature-Store-Build laufen lassen."
        )

    # Saisonprofil je (Wochentag, Feiertag): Median + Quartile (robust ggü. Ausreißern)
    hist["weekday"] = hist["weekday"].astype(int)
    grp = hist.groupby(["weekday", "is_public_holiday"])["visitors"]
    profile = grp.agg(
        median="median",
        q1=lambda s: s.quantile(0.25),
        q3=lambda s: s.quantile(0.75),
    )
    # Globaler Fallback, falls eine Kombination nie vorkam
    global_median = float(hist["visitors"].median())
    global_q1 = float(hist["visitors"].quantile(0.25))
    global_q3 = float(hist["visitors"].quantile(0.75))

    start = date.today() + timedelta(days=1)
    rows = []
    for i in range(horizon):
        d = start + timedelta(days=i)
        weekday = d.isoweekday()  # 1=Mo .. 7=So  (passt zu ISODOW im Feature-Store)
        is_holiday = False        # Feiertage der Zukunft optional via processed.holidays
        key = (weekday, is_holiday)
        if key in profile.index:
            med = float(profile.loc[key, "median"])
            q1 = float(profile.loc[key, "q1"])
            q3 = float(profile.loc[key, "q3"])
        else:
            med, q1, q3 = global_median, global_q1, global_q3
        rows.append({
            "datum": d.isoformat(),
            "forecast": round(med),
            "low": round(max(0.0, q1)),
            "high": round(q3),
        })

    return pd.DataFrame(rows)


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    engine = _engine()
    fc = build_baseline_forecast(engine)
    print("Baseline-Prognose (Kopf):")
    print(fc.head(7).to_string(index=False))

    write_predictions(fc, model_name=MODEL_NAME, model_version=MODEL_VERSION, engine=engine)
    write_staffing_recommendations(fc, model_version=MODEL_VERSION, engine=engine)
    print("\nBaseline-Prognose gespeichert.")


if __name__ == "__main__":
    run()
