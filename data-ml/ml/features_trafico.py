from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from data.paths import PROCESSED

REPO_ROOT = Path(__file__).resolve().parents[2]

FEATURE_COLS = [
    "hour", "dow", "month", "is_rush_hour", "is_weekend",
    "lag_1h", "lag_24h", "lag_168h",
    "temperature_2m", "precipitation",
]
TARGET_COL = "estado_medio"


def build_features(
    trafico_df: pd.DataFrame,
    meteo_df: pd.DataFrame,
    tramo_barrio_df: pd.DataFrame,
) -> pd.DataFrame:
    tf = trafico_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(tf["timestamp"]):
        tf["timestamp"] = pd.to_datetime(tf["timestamp"], utc=True)
    tf["timestamp"] = tf["timestamp"].dt.tz_localize(None) if tf["timestamp"].dt.tz is not None else tf["timestamp"]
    tf["hour_ts"] = tf["timestamp"].dt.floor("h")

    tb = tramo_barrio_df[["idTram", "barrio_id"]].drop_duplicates()
    tf = tf.merge(tb, on="idTram", how="inner")

    agg = (
        tf.groupby(["barrio_id", "hour_ts"])["estatActual"]
        .mean()
        .reset_index()
        .rename(columns={"estatActual": TARGET_COL, "hour_ts": "timestamp"})
    )
    agg = agg.sort_values(["barrio_id", "timestamp"]).reset_index(drop=True)

    agg["hour"] = agg["timestamp"].dt.hour
    agg["dow"] = agg["timestamp"].dt.dayofweek
    agg["month"] = agg["timestamp"].dt.month
    agg["is_rush_hour"] = agg["hour"].isin(list(range(7, 10)) + list(range(17, 21))).astype(int)
    agg["is_weekend"] = (agg["dow"] >= 5).astype(int)

    agg = agg.set_index(["barrio_id", "timestamp"])

    for lag_h, col in [(1, "lag_1h"), (24, "lag_24h"), (168, "lag_168h")]:
        agg[col] = (
            agg.groupby(level="barrio_id")[TARGET_COL]
            .shift(lag_h)
        )

    agg = agg.reset_index()

    for lag_col in ["lag_1h", "lag_24h", "lag_168h"]:
        fill = agg.groupby(["barrio_id", "hour", "dow"])[lag_col].transform("mean")
        agg[lag_col] = agg[lag_col].fillna(fill)
        global_fill = agg.groupby(["barrio_id"])[lag_col].transform("mean")
        agg[lag_col] = agg[lag_col].fillna(global_fill)
        agg[lag_col] = agg[lag_col].fillna(agg[TARGET_COL].mean())

    met = meteo_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(met.iloc[:, 0]):
        time_col = [c for c in met.columns if "time" in c.lower()][0]
        met[time_col] = pd.to_datetime(met[time_col])
    else:
        time_col = met.columns[0]

    met = met.rename(columns={time_col: "timestamp"})
    if met["timestamp"].dt.tz is not None:
        met["timestamp"] = met["timestamp"].dt.tz_localize(None)
    met["timestamp"] = met["timestamp"].dt.floor("h")
    met = met.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    meteo_cols = [c for c in ["temperature_2m", "precipitation"] if c in met.columns]
    met = met[["timestamp"] + meteo_cols]

    agg = pd.merge_asof(
        agg.sort_values("timestamp"),
        met,
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta("2h"),
    )

    for c in meteo_cols:
        agg[c] = agg[c].fillna(agg[c].mean())

    if "temperature_2m" not in agg.columns:
        agg["temperature_2m"] = 15.0
    if "precipitation" not in agg.columns:
        agg["precipitation"] = 0.0

    keep = ["barrio_id", "timestamp", TARGET_COL] + FEATURE_COLS
    agg = agg[keep].dropna(subset=[TARGET_COL]).reset_index(drop=True)

    return agg
