"""Feature engineering para el modelo de accidentes (LightGBM Poisson)."""
from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_COLS = [
    "hour", "dow", "month", "is_rush_hour", "is_weekend",
    "is_holiday", "temperature_2m", "precipitation",
    "barrio_id_enc",
]
TARGET_COL = "n_accidents"


def build_features(
    acc_df: pd.DataFrame,
    meteo_df: pd.DataFrame,
) -> pd.DataFrame:
    df = acc_df.copy()

    # Filtrar registros con barrio conocido (neighborhood_id > 0)
    df["neighborhood_id"] = pd.to_numeric(df["neighborhood_id"], errors="coerce")
    df = df[df["neighborhood_id"] > 0].copy()

    # Construir barrio_id → BAR-XXX (neighborhood_id es 1-73 global)
    df["barrio_id"] = "BAR-" + df["neighborhood_id"].astype(int).astype(str).str.zfill(3)

    # Columnas temporales (year, month, day, hour están en el CSV)
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    df["day"] = df["day"].astype(int)
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce").fillna(0).astype(int)

    df["timestamp"] = pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=df["day"], hour=df["hour"])
    )

    df["dow"] = df["timestamp"].dt.dayofweek
    df["is_rush_hour"] = df["hour"].isin(list(range(7, 10)) + list(range(17, 21))).astype(int)
    df["is_weekend"] = (df["dow"] >= 5).astype(int)

    # Festivos catalanes
    try:
        import holidays
        cat_holidays = holidays.Spain(prov="CT", years=list(df["year"].unique()))
        df["is_holiday"] = df["timestamp"].dt.date.astype(str).isin(
            [str(d) for d in cat_holidays.keys()]
        ).astype(int)
    except Exception:
        df["is_holiday"] = 0

    # Agregar a nivel (barrio_id, year, month, day, hour) → contar accidentes
    grp_cols = ["barrio_id", "timestamp", "year", "month", "day", "hour", "dow",
                "is_rush_hour", "is_weekend", "is_holiday"]
    agg = df.groupby(grp_cols, observed=True).size().reset_index(name=TARGET_COL)

    # Join meteo por timestamp
    met = meteo_df.copy()
    time_col = next(c for c in met.columns if "time" in c.lower())
    met[time_col] = pd.to_datetime(met[time_col])
    if met[time_col].dt.tz is not None:
        met[time_col] = met[time_col].dt.tz_localize(None)
    met[time_col] = met[time_col].dt.floor("h")
    met = met.rename(columns={time_col: "timestamp"})
    met = met.drop_duplicates("timestamp").sort_values("timestamp")

    agg["timestamp"] = pd.to_datetime(agg["timestamp"])
    agg = pd.merge_asof(
        agg.sort_values("timestamp"),
        met[["timestamp", "temperature_2m", "precipitation"]],
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta("2h"),
    )
    agg["temperature_2m"] = agg["temperature_2m"].fillna(agg["temperature_2m"].mean()).fillna(15.0)
    agg["precipitation"] = agg["precipitation"].fillna(0.0)

    # Encoding label del barrio_id
    barrio_enc = {b: i for i, b in enumerate(sorted(agg["barrio_id"].unique()))}
    agg["barrio_id_enc"] = agg["barrio_id"].map(barrio_enc)

    return agg, barrio_enc
