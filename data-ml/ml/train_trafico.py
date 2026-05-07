"""Entrena LightGBM con lags 1h/24h/168h sobre TRAMS por barrio×hora.

Test con últimos 7 días. Output: ml/models/trafico.joblib.
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
from ml.features_trafico import FEATURE_COLS, TARGET_COL, build_features

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODELS_DIR / "trafico.joblib"
TRAMO_BARRIO_PARQUET = PROCESSED / "tramo_barrio.parquet"
TRAFICO_PARQUET = PROCESSED / "trafico.parquet"
RAW_METEO = REPO_ROOT / "meteo.csv"

log = logging.getLogger(__name__)


def _load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trafico_df = pd.read_parquet(TRAFICO_PARQUET)
    tramo_barrio_df = pd.read_parquet(TRAMO_BARRIO_PARQUET)
    meteo_df = pd.read_csv(RAW_METEO, parse_dates=["time"])
    return trafico_df, meteo_df, tramo_barrio_df


def train() -> dict:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    trafico_df, meteo_df, tramo_barrio_df = _load_data()
    log.info("Datos cargados: %d filas tráfico, %d tramos", len(trafico_df), tramo_barrio_df["idTram"].nunique())

    df = build_features(trafico_df, meteo_df, tramo_barrio_df)
    log.info("Features construidas: %d filas, %d barrios", len(df), df["barrio_id"].nunique())

    cutoff = df["timestamp"].max() - pd.Timedelta(days=7)
    train_df = df[df["timestamp"] <= cutoff].copy()
    test_df = df[df["timestamp"] > cutoff].copy()
    log.info("Train: %d filas | Test: %d filas", len(train_df), len(test_df))

    X_train = train_df[FEATURE_COLS].astype(float)
    y_train = train_df[TARGET_COL].astype(float)
    X_test = test_df[FEATURE_COLS].astype(float)
    y_test = test_df[TARGET_COL].astype(float)

    model = LGBMRegressor(
        objective="regression_l1",
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=63,
        n_jobs=4,
        random_state=42,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[],
    )

    y_pred = model.predict(X_test)
    mae = float(np.mean(np.abs(y_pred - y_test.values)))
    spearman_r, _ = spearmanr(y_pred, y_test.values)

    p5 = float(np.percentile(model.predict(X_train), 5))
    p95 = float(np.percentile(model.predict(X_train), 95))

    payload = {
        "model": model,
        "p5": p5,
        "p95": p95,
        "feature_cols": FEATURE_COLS,
        "dow_hour_means": (
            df.groupby(["barrio_id", "dow", "hour"])[TARGET_COL].mean().to_dict()
        ),
        "barrio_ids": sorted(df["barrio_id"].unique().tolist()),
    }
    joblib.dump(payload, MODEL_PATH)
    log.info("Modelo guardado: %s", MODEL_PATH)
    log.info("MAE=%.4f  Spearman=%.4f", mae, spearman_r)

    return {
        "mae": mae,
        "spearman": float(spearman_r),
        "n_barrios": int(df["barrio_id"].nunique()),
    }


def predict_48h(
    model_payload: dict,
    tramo_barrio_df: pd.DataFrame,
    meteo_df: pd.DataFrame,
) -> pd.DataFrame:
    model = model_payload["model"]
    p5: float = model_payload["p5"]
    p95: float = model_payload["p95"]
    feature_cols: list[str] = model_payload["feature_cols"]
    dow_hour_means: dict = model_payload["dow_hour_means"]
    barrio_ids: list[str] = model_payload["barrio_ids"]

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    timestamps = [now + timedelta(hours=h) for h in range(48)]
    ts_naive = [t.replace(tzinfo=None) for t in timestamps]

    met = meteo_df.copy()
    time_col = [c for c in met.columns if "time" in c.lower()][0]
    if not pd.api.types.is_datetime64_any_dtype(met[time_col]):
        met[time_col] = pd.to_datetime(met[time_col])
    met = met.rename(columns={time_col: "timestamp"})
    if met["timestamp"].dt.tz is not None:
        met["timestamp"] = met["timestamp"].dt.tz_localize(None)
    met["timestamp"] = met["timestamp"].dt.floor("h")
    met = met.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    rows = []
    for bid in barrio_ids:
        for ts in ts_naive:
            hour = ts.hour
            dow = ts.weekday()
            month = ts.month
            is_rush = int(hour in list(range(7, 10)) + list(range(17, 21)))
            is_weekend = int(dow >= 5)

            proxy = dow_hour_means.get((bid, dow, hour), None)
            if proxy is None:
                proxy = np.mean(list(dow_hour_means.values())) if dow_hour_means else 3.0

            row = {
                "barrio_id": bid,
                "timestamp": ts,
                "hour": hour,
                "dow": dow,
                "month": month,
                "is_rush_hour": is_rush,
                "is_weekend": is_weekend,
                "lag_1h": proxy,
                "lag_24h": proxy,
                "lag_168h": proxy,
                "temperature_2m": np.nan,
                "precipitation": np.nan,
            }
            rows.append(row)

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
        pred_df[col] = pred_df[col].fillna(pred_df[col].mean()).fillna(0.0)

    X = pred_df[feature_cols].astype(float)
    raw_scores = model.predict(X)

    span = p95 - p5 if p95 > p5 else 1.0
    normalized = np.clip((raw_scores - p5) / span, 0.0, 1.0)

    out = pred_df[["barrio_id", "timestamp"]].copy()
    out["score_trafico"] = normalized.astype(float)
    out["timestamp"] = pd.to_datetime(out["timestamp"]).dt.tz_localize("UTC")
    return out.sort_values(["timestamp", "barrio_id"]).reset_index(drop=True)


def main() -> None:
    result = train()
    print(f"MAE={result['mae']:.4f}  Spearman={result['spearman']:.4f}  barrios={result['n_barrios']}")


if __name__ == "__main__":
    main()
