"""
models(Nico)/ml_forecast.py
Version 2: Eigenständiger Besucher-Forecast OHNE futureEXPERT.

Ansatz
------
Gradient Boosting (scikit-learn, HistGradientBoostingRegressor) mit
Quantil-Verlustfunktion: drei Modelle für die Quantile 0.1 / 0.5 / 0.9
liefern Punktprognose UND ein echtes 80%-Prognoseintervall – statt eines
symmetrischen ±x%-Bands.

Features:
  * Kalender: Wochentag, Wochenende, Monat, Jahrestag (sin/cos, zyklisch),
    Feiertag + Brückentag (holidays-Paket, Bayern)
  * Autoregressiv: Lags 1/7/14, rollierende Mittel 7/28 Tage
  * Wetter: Temperatur & Niederschlag – historisch aus raw.weather, für die
    Zukunft aus dem eigenen Wetter-Forecast (weather_forecast.py)

Zwei Horizonte wie beim futureEXPERT-Lauf:
  * Tag 1–10:  "detail" – echte Wettervorhersage als Feature
  * Tag 11–30: "grob"   – Klimatologie statt Wettervorhersage; die Prognose
    ist rekursiv (eigene Vorhersagen speisen die Lag-Features), die Unsicherheit
    wächst also sichtbar mit dem Horizont.

Evaluation: Rollierender Backtest (Rolling Origin, 4 Folds à 7 Tage) mit
MAE / RMSE / MAPE gegen die Seasonal-Naive-Baseline (Wert der Vorwoche) und
Coverage-Check des 80%-Intervalls. Ergebnisse in ml_backtest_metrics.csv.

Aufruf:
    python "models(Nico)/ml_forecast.py"
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forecast_db import write_predictions, write_staffing_recommendations  # noqa: E402
from hourly_profile import disaggregate, load_profile  # noqa: E402
from weather_forecast import get_weather_future  # noqa: E402

logger = logging.getLogger(__name__)

MODEL_NAME = "ml-gradient-boosting"
MODEL_VERSION = "hgb-quantile-v1"
HORIZON_DETAIL = 10
HORIZON_COARSE = 30
QUANTILES = (0.1, 0.5, 0.9)          # 80%-Prognoseintervall
MIN_HISTORY_DAYS = 60                # darunter ist Training nicht seriös
BACKTEST_FOLDS = 4
BACKTEST_HORIZON = 7

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FEATURES = [
    "weekday", "is_weekend", "is_holiday", "is_bridge_day",
    "month", "doy_sin", "doy_cos",
    "lag_1", "lag_7", "lag_14", "roll_7", "roll_28",
    "temperature_c", "precipitation_mm", "is_rainy",
]


# ── Daten laden ──────────────────────────────────────────────────────────────

def _engine():
    load_dotenv()
    for name in ("DATABASE_URL_DS", "DATABASE_URL_ETL"):
        url = os.environ.get(name)
        if not url or "ep-xxx" in url:
            continue
        eng = create_engine(url, pool_pre_ping=True)
        try:
            with eng.connect() as c:
                c.execute(text("SELECT 1"))
            print(f"  Verbunden über {name}")
            return eng
        except Exception as exc:
            print(f"  WARN: {name} nicht nutzbar ({str(exc)[:90]})")
    raise RuntimeError(
        "Keine der Datenbank-URLs aus der .env funktioniert. "
        "Bitte URLs prüfen (Host/Passwort) – siehe .env im Projektroot."
    )


def load_daily(engine) -> pd.DataFrame:
    """Tagesbesucher + Tageswetter aus raw.* (wie futureexpert_forecast.py)."""
    with engine.connect() as conn:
        visitors = pd.read_sql(text("""
            SELECT timestamp_local, count_enter
            FROM raw.library_visitors ORDER BY timestamp_local
        """), conn)
        weather = pd.read_sql(text("""
            SELECT timestamp_local, temperature_c, precipitation_mm
            FROM raw.weather ORDER BY timestamp_local
        """), conn)

    visitors["timestamp_local"] = pd.to_datetime(visitors["timestamp_local"], utc=True)
    weather["timestamp_local"] = pd.to_datetime(weather["timestamp_local"], utc=True)

    v = (visitors.groupby(visitors["timestamp_local"].dt.date)["count_enter"]
         .sum().rename("besucher"))
    w = (weather.groupby(weather["timestamp_local"].dt.date)
         .agg(temperature_c=("temperature_c", "mean"),
              precipitation_mm=("precipitation_mm", "sum")))

    df = pd.concat([v, w], axis=1).reset_index(names="datum")
    df["datum"] = pd.to_datetime(df["datum"])
    df = df.dropna(subset=["besucher"]).sort_values("datum").reset_index(drop=True)
    # Wetterlücken konservativ füllen (Vortageswert), damit kein Tag verloren geht
    df[["temperature_c", "precipitation_mm"]] = (
        df[["temperature_c", "precipitation_mm"]].ffill().bfill()
    )
    return df


# ── Feature Engineering ──────────────────────────────────────────────────────

def _holiday_calendar(years: list[int]):
    import holidays as hol
    return hol.Germany(subdiv="BY", years=years)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Kalender-, Wetter- und Lag-Features für Trainingsdaten (mit besucher)."""
    out = df.copy()
    cal = _holiday_calendar(sorted(out["datum"].dt.year.unique().tolist()))

    out["weekday"] = out["datum"].dt.dayofweek + 1  # 1=Mo .. 7=So (ISO)
    out["is_weekend"] = (out["weekday"] >= 6).astype(int)
    out["month"] = out["datum"].dt.month
    doy = out["datum"].dt.dayofyear
    out["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    out["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    out["is_holiday"] = out["datum"].dt.date.map(lambda d: int(d in cal))
    out["is_bridge_day"] = out["datum"].dt.date.map(
        lambda d: int(d not in cal and (
            (d - timedelta(days=1)) in cal or (d + timedelta(days=1)) in cal
        ) and pd.Timestamp(d).isoweekday() <= 5)
    )
    out["is_rainy"] = (out["precipitation_mm"] > 1.0).astype(int)

    out["lag_1"] = out["besucher"].shift(1)
    out["lag_7"] = out["besucher"].shift(7)
    out["lag_14"] = out["besucher"].shift(14)
    out["roll_7"] = out["besucher"].shift(1).rolling(7).mean()
    out["roll_28"] = out["besucher"].shift(1).rolling(28, min_periods=14).mean()
    return out.dropna(subset=["lag_14", "roll_7"]).reset_index(drop=True)


# ── Training & rekursive Prognose ────────────────────────────────────────────

def train_quantile_models(train: pd.DataFrame) -> dict[float, object]:
    from sklearn.ensemble import HistGradientBoostingRegressor
    models: dict[float, object] = {}
    for q in QUANTILES:
        m = HistGradientBoostingRegressor(
            loss="quantile", quantile=q,
            max_depth=4, learning_rate=0.08, max_iter=300,
            min_samples_leaf=10, random_state=42,
            categorical_features=["weekday", "month"],
        )
        m.fit(train[FEATURES], train["besucher"])
        models[q] = m
    return models


def recursive_forecast(history: pd.DataFrame, weather_future: pd.DataFrame,
                       models: dict[float, object], horizon: int) -> pd.DataFrame:
    """
    Prognostiziert `horizon` Tage rekursiv: Die Median-Prognose jedes Tages
    wird zur Historie hinzugefügt, damit Lag-/Rolling-Features der Folgetage
    berechnet werden können.
    """
    cal = _holiday_calendar(sorted({history["datum"].dt.year.max(),
                                    history["datum"].dt.year.max() + 1}))
    values = history["besucher"].tolist()
    wmap = weather_future.set_index(weather_future["datum"].dt.date)

    rows: list[dict] = []
    start = history["datum"].max() + timedelta(days=1)
    for i in range(horizon):
        d = (start + timedelta(days=i))
        day = d.date()
        if day in wmap.index:
            temp = float(wmap.loc[day, "temperature_c"])
            prec = float(wmap.loc[day, "precipitation_mm"])
        else:  # sollte durch get_weather_future nie passieren
            temp, prec = 15.0, 1.5

        doy = pd.Timestamp(d).dayofyear
        feats = {
            "weekday": d.isoweekday(),
            "is_weekend": int(d.isoweekday() >= 6),
            "is_holiday": int(day in cal),
            "is_bridge_day": int(day not in cal and (
                (day - timedelta(days=1)) in cal or (day + timedelta(days=1)) in cal
            ) and d.isoweekday() <= 5),
            "month": d.month,
            "doy_sin": np.sin(2 * np.pi * doy / 365.25),
            "doy_cos": np.cos(2 * np.pi * doy / 365.25),
            "lag_1": values[-1],
            "lag_7": values[-7],
            "lag_14": values[-14],
            "roll_7": float(np.mean(values[-7:])),
            "roll_28": float(np.mean(values[-28:])),
            "temperature_c": temp,
            "precipitation_mm": prec,
            "is_rainy": int(prec > 1.0),
        }
        x = pd.DataFrame([feats])[FEATURES]
        q10, q50, q90 = (float(models[q].predict(x)[0]) for q in QUANTILES)
        lo, med, hi = sorted((q10, q50, q90))  # Quantil-Crossing absichern
        lo, med, hi = max(0.0, lo), max(0.0, med), max(0.0, hi)

        rows.append({
            "datum": d.date().isoformat(),
            "forecast": round(med),
            "low": round(lo),
            "high": round(hi),
            "horizont": "detail" if i < HORIZON_DETAIL else "grob",
        })
        values.append(med)  # Rekursion: Prognose wird Input der Folgetage

    return pd.DataFrame(rows)


# ── Backtest (Rolling Origin) ────────────────────────────────────────────────

def backtest(feat: pd.DataFrame) -> pd.DataFrame:
    """
    Rolling-Origin-Backtest: BACKTEST_FOLDS Ursprünge im Wochenabstand am Ende
    der Historie, je BACKTEST_HORIZON Tage Vorhersage. Vergleich gegen
    Seasonal-Naive (Wert der Vorwoche). Wetter = beobachtete Werte
    (Backtest misst die Modellgüte, nicht die Wetterprognosegüte).
    """
    results: list[dict] = []
    n = len(feat)
    for fold in range(BACKTEST_FOLDS):
        cut = n - (BACKTEST_FOLDS - fold) * BACKTEST_HORIZON
        if cut < MIN_HISTORY_DAYS:
            continue
        train, test = feat.iloc[:cut], feat.iloc[cut:cut + BACKTEST_HORIZON]
        models = train_quantile_models(train)
        preds = {q: models[q].predict(test[FEATURES]) for q in QUANTILES}

        y = test["besucher"].to_numpy(dtype=float)
        p = np.maximum(np.asarray(preds[0.5], dtype=float), 0.0)
        naive = test["lag_7"].to_numpy(dtype=float)
        lo = np.minimum(preds[0.1], preds[0.9])
        hi = np.maximum(preds[0.1], preds[0.9])
        nonzero = y > 0
        results.append({
            "fold": fold + 1,
            "test_start": str(test["datum"].iloc[0].date()),
            "mae_ml": float(np.mean(np.abs(y - p))),
            "mae_naive": float(np.mean(np.abs(y - naive))),
            "rmse_ml": float(np.sqrt(np.mean((y - p) ** 2))),
            "rmse_naive": float(np.sqrt(np.mean((y - naive) ** 2))),
            "mape_ml_pct": float(np.mean(np.abs((y[nonzero] - p[nonzero]) / y[nonzero])) * 100)
            if nonzero.any() else np.nan,
            "coverage_80_pct": float(np.mean((y >= lo) & (y <= hi)) * 100),
        })
    return pd.DataFrame(results)


# ── Hauptlauf ────────────────────────────────────────────────────────────────

def run() -> None:
    logging.basicConfig(level=logging.INFO)
    engine = _engine()

    print("Lade Daten aus Neon DB...")
    daily = load_daily(engine)
    print(f"  {len(daily)} Tage Historie "
          f"({daily['datum'].min().date()} – {daily['datum'].max().date()})")
    last_day = daily["datum"].max().date()
    if last_day < date.today() - timedelta(days=1):
        print(f"  WARN: Besucherdaten enden am {last_day} – der Forecast beginnt "
              f"dort, nicht heute! Zuerst die ETL-Pipeline laufen lassen: "
              f"python -m etl.pipeline")
    if len(daily) < MIN_HISTORY_DAYS:
        raise RuntimeError(
            f"Nur {len(daily)} Tage Historie – Minimum sind {MIN_HISTORY_DAYS}. "
            "Bitte zuerst die ETL-Pipeline vollständig laufen lassen."
        )

    feat = build_features(daily)

    # 1) Backtest – ehrliche Gütemessung VOR der eigentlichen Prognose
    print("\nBacktest (Rolling Origin)...")
    bt = backtest(feat)
    if not bt.empty:
        print(bt.round(1).to_string(index=False))
        print(f"\n  Ø MAE  ML vs. Naive: {bt['mae_ml'].mean():.1f} vs. "
              f"{bt['mae_naive'].mean():.1f}")
        print(f"  Ø Coverage 80%-Intervall: {bt['coverage_80_pct'].mean():.0f}% "
              "(Soll: ~80%)")
        bt_path = os.path.join(BASE_DIR, "ml_backtest_metrics.csv")
        bt.to_csv(bt_path, index=False)
        print(f"  Gespeichert: {bt_path}")

    # 2) Finales Training auf der GESAMTEN Historie
    print("\nTrainiere finale Quantil-Modelle (q=0.1/0.5/0.9)...")
    models = train_quantile_models(feat)

    # 3) Wetter-Forecast holen und 30 Tage rekursiv prognostizieren
    print("Hole Wetter-Forecast...")
    weather_future = get_weather_future(HORIZON_COARSE)
    fc = recursive_forecast(daily, weather_future, models, HORIZON_COARSE)

    print(f"\nPrognose (Tag 1–{HORIZON_DETAIL} = detail, danach grob):")
    print(fc.head(HORIZON_DETAIL).to_string(index=False))

    out_path = os.path.join(BASE_DIR, "forecast_besucher_ml.csv")
    fc.to_csv(out_path, index=False)
    print(f"\nGespeichert: {out_path}")

    # 4) Stunden-Forecast
    profile = load_profile(engine)
    hourly_fc = disaggregate(fc, profile)
    hourly_path = os.path.join(BASE_DIR, "forecast_besucher_ml_stuendlich.csv")
    hourly_fc.to_csv(hourly_path, index=False)
    print(f"Stunden-Forecast: {len(hourly_fc)} Stundenwerte -> {hourly_path}")

    # 5) In die DB schreiben – als eigenes Modell neben futureEXPERT.
    #    Staffing-Empfehlungen bleiben standardmäßig dem führenden
    #    futureEXPERT-Lauf vorbehalten (ML_WRITE_STAFFING=1 zum Überschreiben).
    try:
        write_predictions(fc, model_name=MODEL_NAME, model_version=MODEL_VERSION,
                          engine=engine)
        if os.environ.get("ML_WRITE_STAFFING", "0") == "1":
            write_staffing_recommendations(fc, model_version=MODEL_VERSION,
                                           engine=engine, hourly_profile=profile)
    except Exception as exc:
        print(f"  WARN: DB-Write fehlgeschlagen ({exc}). CSV bleibt nutzbar.")

    print("\nFertig!")


if __name__ == "__main__":
    run()
