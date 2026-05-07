"""Entrena LightGBM Poisson sobre dataset de accidentes BCN.

Split temporal: años 2010-2019 train, 2020-2021 test.
Output: ml/models/accidentes.joblib
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from scipy.stats import spearmanr

from data.paths import PROCESSED
from ml.features_accidentes import FEATURE_COLS, TARGET_COL, build_features

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODELS_DIR / "accidentes.joblib"
ACC_CSV = REPO_ROOT / "accidents_opendata.csv"
RAW_METEO = REPO_ROOT / "meteo.csv"

log = logging.getLogger(__name__)


def train() -> dict:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    log.info("Cargando dataset accidentes...")
    acc_df = pd.read_csv(ACC_CSV, encoding="utf-8", low_memory=False)
    log.info("Accidentes: %d filas, años %s-%s", len(acc_df), acc_df["year"].min(), acc_df["year"].max())

    meteo_df = pd.read_csv(RAW_METEO, parse_dates=["time"])

    log.info("Construyendo features...")
    df, barrio_enc = build_features(acc_df, meteo_df)
    log.info("Features: %d filas, %d barrios", len(df), df["barrio_id"].nunique())

    train_df = df[df["year"] <= 2019].copy()
    test_df = df[df["year"] >= 2020].copy()
    log.info("Train: %d filas | Test: %d filas", len(train_df), len(test_df))

    X_train = train_df[FEATURE_COLS].astype(float)
    y_train = train_df[TARGET_COL].astype(float)
    X_test = test_df[FEATURE_COLS].astype(float)
    y_test = test_df[TARGET_COL].astype(float)

    model = LGBMRegressor(
        objective="poisson",
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=63,
        n_jobs=4,
        random_state=42,
        min_child_samples=5,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)])

    y_pred = model.predict(X_test)
    mae = float(np.mean(np.abs(y_pred - y_test.values)))
    spearman_r, _ = spearmanr(y_pred, y_test.values)

    # Percentiles para normalización
    all_preds = model.predict(X_train)
    p5 = float(np.percentile(all_preds, 5))
    p95 = float(np.percentile(all_preds, 95))

    payload = {
        "model": model,
        "p5": p5,
        "p95": p95,
        "feature_cols": FEATURE_COLS,
        "barrio_enc": barrio_enc,
        "barrio_ids": sorted(df["barrio_id"].unique().tolist()),
        "dow_hour_barrio_means": (
            df.groupby(["barrio_id", "dow", "hour"])[TARGET_COL].mean().to_dict()
        ),
    }
    joblib.dump(payload, MODEL_PATH)
    log.info("Modelo guardado: %s  MAE=%.4f  Spearman=%.4f", MODEL_PATH, mae, spearman_r)
    return {"mae": mae, "spearman": float(spearman_r), "n_barrios": int(df["barrio_id"].nunique())}


def predict_48h(model_payload: dict, meteo_df: pd.DataFrame) -> pd.DataFrame:
    model = model_payload["model"]
    p5: float = model_payload["p5"]
    p95: float = model_payload["p95"]
    feature_cols: list[str] = model_payload["feature_cols"]
    barrio_enc: dict = model_payload["barrio_enc"]
    barrio_ids: list[str] = model_payload["barrio_ids"]
    dow_hour_barrio_means: dict = model_payload["dow_hour_barrio_means"]

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    timestamps = [now + timedelta(hours=h) for h in range(48)]

    try:
        import holidays
        cat_hols = holidays.Spain(prov="CT", years=[now.year, now.year + 1])
        holiday_dates = {str(d) for d in cat_hols.keys()}
    except Exception:
        holiday_dates = set()

    met = meteo_df.copy()
    time_col = next(c for c in met.columns if "time" in c.lower())
    met[time_col] = pd.to_datetime(met[time_col])
    if met[time_col].dt.tz is not None:
        met[time_col] = met[time_col].dt.tz_localize(None)
    met[time_col] = met[time_col].dt.floor("h")
    met = met.rename(columns={time_col: "timestamp"}).drop_duplicates("timestamp")

    rows = []
    for bid in barrio_ids:
        enc = barrio_enc.get(bid, 0)
        for ts in timestamps:
            ts_naive = ts.replace(tzinfo=None)
            hour = ts.hour
            dow = ts.weekday()
            month = ts.month
            is_rush = int(hour in list(range(7, 10)) + list(range(17, 21)))
            is_weekend = int(dow >= 5)
            is_holiday = int(str(ts.date()) in holiday_dates)
            proxy = dow_hour_barrio_means.get((bid, dow, hour), 0.1)
            rows.append({
                "barrio_id": bid,
                "timestamp": ts_naive,
                "hour": hour,
                "dow": dow,
                "month": month,
                "is_rush_hour": is_rush,
                "is_weekend": is_weekend,
                "is_holiday": is_holiday,
                "barrio_id_enc": enc,
                "temperature_2m": np.nan,
                "precipitation": np.nan,
            })

    pred_df = pd.DataFrame(rows)
    pred_df = pd.merge_asof(
        pred_df.sort_values("timestamp"),
        met[["timestamp", "temperature_2m", "precipitation"]],
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta("2h"),
        suffixes=("_x", ""),
    )
    for col in ["temperature_2m", "precipitation"]:
        x_col = col + "_x"
        if x_col in pred_df.columns:
            pred_df[col] = pred_df[col].fillna(pred_df[x_col])
            pred_df = pred_df.drop(columns=[x_col])
        pred_df[col] = pred_df[col].fillna(15.0 if "temp" in col else 0.0)

    X = pred_df[feature_cols].astype(float)
    raw_scores = model.predict(X)
    span = p95 - p5 if p95 > p5 else 1.0
    normalized = np.clip((raw_scores - p5) / span, 0.0, 1.0)

    out = pred_df[["barrio_id", "timestamp"]].copy()
    out["score_accidentes"] = normalized.astype(float)
    out["timestamp"] = pd.to_datetime(out["timestamp"]).dt.tz_localize("UTC")
    return out.sort_values(["timestamp", "barrio_id"]).reset_index(drop=True)


def main() -> None:
    result = train()
    print(f"MAE={result['mae']:.4f}  Spearman={result['spearman']:.4f}  barrios={result['n_barrios']}")


if __name__ == "__main__":
    main()
