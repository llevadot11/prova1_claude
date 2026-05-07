"""Pipeline de scoring → data/processed/ufi_latest.parquet.

Salida (schema fijo, NO romper sin avisar a B):
    barrio_id: str
    timestamp: datetime (UTC, hora redondeada)
    ufi_default: float (0-100)
    score_trafico: float (0-1)
    score_accidentes: float (0-1)
    score_aire: float (0-1)
    score_meteo: float (0-1)
    score_sensibilidad: float (0-1)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from data.paths import PROCESSED, RAW_AIRE, RAW_METEO, UFI_PARQUET

MODELS_DIR = Path(__file__).resolve().parent / "models"
TRAMO_BARRIO = PROCESSED / "tramo_barrio.parquet"
HOSPITALES = PROCESSED / "hospitales_bcn.parquet"
AIRE_73 = PROCESSED / "aire_73pts.parquet"
METEO_73 = PROCESSED / "meteo_73pts.parquet"

log = logging.getLogger(__name__)

FAMILIES = ("trafico", "accidentes", "aire", "meteo", "sensibilidad")
N_BARRIOS = 73
HORIZON_HOURS = 48
BARRIO_IDS = [f"BAR-{i:03d}" for i in range(1, N_BARRIOS + 1)]


def _robust_minmax(s: pd.Series, p_low: float = 5.0, p_high: float = 95.0) -> pd.Series:
    lo = np.percentile(s.dropna(), p_low)
    hi = np.percentile(s.dropna(), p_high)
    span = hi - lo if hi > lo else 1.0
    return ((s - lo) / span).clip(0.0, 1.0)


def _score_meteo_and_aire(now: datetime) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve score_meteo y score_aire para 73 barrios × 48h desde los Parquets 73pts."""
    timestamps = pd.date_range(now, periods=HORIZON_HOURS, freq="h", tz="UTC")

    def _load_and_filter(path: Path, fallback_path: Path) -> pd.DataFrame:
        if path.exists():
            df = pd.read_parquet(path)
            df["time"] = pd.to_datetime(df["time"], utc=True)
            df = df[df["time"].isin(timestamps)]
            return df
        # Fallback: single-point replicado para los 73 barrios
        df = pd.read_csv(fallback_path, parse_dates=["time"])
        df["time"] = df["time"].dt.tz_localize("UTC")
        df = df[df["time"].isin(timestamps)]
        rows = []
        for bid in BARRIO_IDS:
            tmp = df.copy()
            tmp["barrio_id"] = bid
            rows.append(tmp)
        return pd.concat(rows, ignore_index=True)

    meteo = _load_and_filter(METEO_73, RAW_METEO)
    aire = _load_and_filter(AIRE_73, RAW_AIRE)

    def _make_score_meteo(df: pd.DataFrame) -> pd.DataFrame:
        # Score meteo: combinación de precipitación y viento
        # Más lluvia y más viento → más fricción
        if "precipitation" in df.columns:
            prec_score = (df["precipitation"].clip(0, 20) / 20.0)
        else:
            prec_score = pd.Series(0.0, index=df.index)
        if "wind_speed_10m" in df.columns:
            wind_score = (df["wind_speed_10m"].clip(0, 50) / 50.0)
        else:
            wind_score = pd.Series(0.0, index=df.index)
        df = df.copy()
        df["score_meteo"] = (0.7 * prec_score + 0.3 * wind_score).clip(0.0, 1.0)
        return df[["barrio_id", "time", "score_meteo"]].rename(columns={"time": "timestamp"})

    def _make_score_aire(df: pd.DataFrame) -> pd.DataFrame:
        # Score aire: combinación ponderada de pm10, no2, ozone
        df = df.copy()
        pm10 = df.get("pm10", pd.Series(0.0, index=df.index)).fillna(0).clip(0, 150) / 150.0
        no2 = df.get("nitrogen_dioxide", pd.Series(0.0, index=df.index)).fillna(0).clip(0, 200) / 200.0
        ozone = df.get("ozone", pd.Series(0.0, index=df.index)).fillna(0).clip(0, 180) / 180.0
        df["score_aire"] = (0.4 * pm10 + 0.4 * no2 + 0.2 * ozone).clip(0.0, 1.0)
        return df[["barrio_id", "time", "score_aire"]].rename(columns={"time": "timestamp"})

    return _make_score_meteo(meteo), _make_score_aire(aire)


def _score_sensibilidad() -> pd.DataFrame:
    """Score estático basado en densidad de POIs (hospitales + colegios) por barrio."""
    pois_path = PROCESSED / "pois_per_barrio.parquet"
    all_barrios = pd.DataFrame({"barrio_id": BARRIO_IDS})

    # Usar POIs descargados si existen y tienen datos
    if pois_path.exists():
        pois = pd.read_parquet(pois_path)
        if pois["score_sensibilidad"].max() > 0.1:
            all_barrios = all_barrios.merge(pois[["barrio_id", "score_sensibilidad"]], on="barrio_id", how="left")
            all_barrios["score_sensibilidad"] = all_barrios["score_sensibilidad"].fillna(0.05)
            return all_barrios[["barrio_id", "score_sensibilidad"]]

    # Fallback: hospitales limpios ya descargados
    if HOSPITALES.exists():
        import geopandas as gpd
        hosp = pd.read_parquet(HOSPITALES)
        barrios_gj = gpd.read_file(PROCESSED / "barrios.geojson").set_crs(epsg=4326)
        hosp_gdf = gpd.GeoDataFrame(
            hosp,
            geometry=gpd.points_from_xy(hosp["lon"], hosp["lat"]),
            crs="EPSG:4326",
        )
        joined = gpd.sjoin(hosp_gdf, barrios_gj[["barrio_id", "geometry"]], how="left", predicate="within")
        hosp_per_barrio = joined.groupby("barrio_id").size().reset_index(name="n_hospitales")
        all_barrios = all_barrios.merge(hosp_per_barrio, on="barrio_id", how="left")
        all_barrios["n_hospitales"] = all_barrios["n_hospitales"].fillna(0).astype(int)
        max_h = all_barrios["n_hospitales"].max()
        all_barrios["score_sensibilidad"] = (
            (all_barrios["n_hospitales"] / max_h).clip(0.0, 1.0) if max_h > 0 else 0.1
        )
    else:
        all_barrios["score_sensibilidad"] = 0.1

    return all_barrios[["barrio_id", "score_sensibilidad"]]


def real_scores(now: datetime) -> pd.DataFrame:
    """Genera scores reales con modelos LightGBM."""
    timestamps = [now + timedelta(hours=h) for h in range(HORIZON_HOURS)]

    # --- Tráfico ---
    trafico_path = MODELS_DIR / "trafico.joblib"
    if trafico_path.exists():
        trafico_payload = joblib.load(trafico_path)
        from ml.train_trafico import predict_48h as pred_trafico
        tramo_barrio_df = pd.read_parquet(TRAMO_BARRIO)
        meteo_df = pd.read_csv(RAW_METEO, parse_dates=["time"])
        score_trafico_df = pred_trafico(trafico_payload, tramo_barrio_df, meteo_df)
    else:
        score_trafico_df = None

    # --- Accidentes ---
    acc_path = MODELS_DIR / "accidentes.joblib"
    if acc_path.exists():
        acc_payload = joblib.load(acc_path)
        from ml.train_accidentes import predict_48h as pred_acc
        meteo_df2 = pd.read_csv(RAW_METEO, parse_dates=["time"])
        score_acc_df = pred_acc(acc_payload, meteo_df2)
    else:
        score_acc_df = None

    # --- Meteo + Aire (73 pts) ---
    score_meteo_df, score_aire_df = _score_meteo_and_aire(now)

    # --- Sensibilidad (estático) ---
    sens_df = _score_sensibilidad()

    # Base: todos los barrios × todas las horas
    base_rows = []
    for ts in timestamps:
        for bid in BARRIO_IDS:
            base_rows.append({"barrio_id": bid, "timestamp": ts})
    base = pd.DataFrame(base_rows)
    base["timestamp"] = pd.to_datetime(base["timestamp"])
    if base["timestamp"].dt.tz is None:
        base["timestamp"] = base["timestamp"].dt.tz_localize("UTC")

    # Merge score_trafico
    if score_trafico_df is not None:
        base = base.merge(
            score_trafico_df[["barrio_id", "timestamp", "score_trafico"]],
            on=["barrio_id", "timestamp"], how="left",
        )
    if "score_trafico" not in base.columns:
        base["score_trafico"] = 0.3

    # Barrios sin modelo de tráfico (no hay TRAMS): rellenar con media de barrios con datos
    trafico_mean = base[base["score_trafico"] > 0]["score_trafico"].mean()
    base["score_trafico"] = base["score_trafico"].fillna(trafico_mean if not np.isnan(trafico_mean) else 0.3)

    # Merge score_accidentes
    if score_acc_df is not None:
        base = base.merge(
            score_acc_df[["barrio_id", "timestamp", "score_accidentes"]],
            on=["barrio_id", "timestamp"], how="left",
        )
    if "score_accidentes" not in base.columns:
        base["score_accidentes"] = 0.2
    base["score_accidentes"] = base["score_accidentes"].fillna(0.2)

    # Merge score_meteo
    score_meteo_df["timestamp"] = pd.to_datetime(score_meteo_df["timestamp"])
    if score_meteo_df["timestamp"].dt.tz is None:
        score_meteo_df["timestamp"] = score_meteo_df["timestamp"].dt.tz_localize("UTC")
    base = base.merge(
        score_meteo_df[["barrio_id", "timestamp", "score_meteo"]],
        on=["barrio_id", "timestamp"], how="left",
    )
    base["score_meteo"] = base["score_meteo"].fillna(0.0)

    # Merge score_aire
    score_aire_df["timestamp"] = pd.to_datetime(score_aire_df["timestamp"])
    if score_aire_df["timestamp"].dt.tz is None:
        score_aire_df["timestamp"] = score_aire_df["timestamp"].dt.tz_localize("UTC")
    base = base.merge(
        score_aire_df[["barrio_id", "timestamp", "score_aire"]],
        on=["barrio_id", "timestamp"], how="left",
    )
    base["score_aire"] = base["score_aire"].fillna(0.1)

    # Merge score_sensibilidad (estático)
    base = base.merge(sens_df, on="barrio_id", how="left")
    base["score_sensibilidad"] = base["score_sensibilidad"].fillna(0.1)

    return base


def fuse(scores: pd.DataFrame) -> pd.DataFrame:
    """Aplica pesos default y normaliza a 0-100."""
    weights = {
        "trafico": 0.30,
        "accidentes": 0.25,
        "aire": 0.20,
        "meteo": 0.15,
        "sensibilidad": 0.10,
    }
    raw = sum(weights[f] * scores[f"score_{f}"] for f in FAMILIES)
    scores = scores.assign(_raw=raw)
    # z-score por hora → sigmoide → 0-100
    grp = scores.groupby("timestamp")["_raw"]
    z = (scores["_raw"] - grp.transform("mean")) / grp.transform("std").replace(0, 1)
    scores["ufi_default"] = (1 / (1 + np.exp(-z))) * 100
    return scores.drop(columns=["_raw"])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    PROCESSED.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    use_real = (MODELS_DIR / "trafico.joblib").exists() and (MODELS_DIR / "accidentes.joblib").exists()

    if use_real:
        log.info("Usando modelos reales LightGBM...")
        scores = real_scores(now)
    else:
        log.info("Modelos no encontrados, usando heurístico stub...")
        rng = np.random.default_rng(42)
        rows = []
        for h in range(HORIZON_HOURS):
            ts = now + timedelta(hours=h)
            for i in range(1, N_BARRIOS + 1):
                row = {"barrio_id": f"BAR-{i:03d}", "timestamp": ts}
                for fam in FAMILIES:
                    row[f"score_{fam}"] = float(rng.random())
                rows.append(row)
        scores = pd.DataFrame(rows)

    out = fuse(scores)

    # Garantizar schema correcto
    for col in ["score_trafico", "score_accidentes", "score_aire", "score_meteo", "score_sensibilidad"]:
        out[col] = out[col].astype(float).clip(0.0, 1.0)
    out["ufi_default"] = out["ufi_default"].astype(float).clip(0.0, 100.0)
    out["barrio_id"] = out["barrio_id"].astype(str)

    cols = ["barrio_id", "timestamp", "ufi_default",
            "score_trafico", "score_accidentes", "score_aire", "score_meteo", "score_sensibilidad"]
    out = out[cols]
    out.to_parquet(UFI_PARQUET, index=False)
    log.info("UFI escrito: %s (%d filas)", UFI_PARQUET, len(out))


if __name__ == "__main__":
    main()
