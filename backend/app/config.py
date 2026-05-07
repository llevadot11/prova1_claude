from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_aq_url: str = "https://air-quality-api.open-meteo.com/v1/air-quality"

    # Comma-separated origins for CORS. "*" = open (local dev default).
    # In production set to the Vercel URL, e.g. "https://ufi-bcn.vercel.app"
    cors_origins: str = "*"

    demo_offline: bool = False

    repo_root: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = Path("data")
    processed_dir: Path = Path("data/processed")
    cache_dir: Path = Path("data/cache")

    @property
    def ufi_parquet(self) -> Path:
        return self.repo_root / self.processed_dir / "ufi_latest.parquet"

    @property
    def barrios_geojson(self) -> Path:
        return self.repo_root / self.processed_dir / "barrios.geojson"

    @property
    def tramos_geojson(self) -> Path:
        return self.repo_root / self.processed_dir / "tramos.geojson"

    @property
    def cache_db(self) -> Path:
        return self.repo_root / self.cache_dir / "api_cache.sqlite"

    @property
    def snapshot_json(self) -> Path:
        return self.repo_root / self.processed_dir / "snapshot.json"


settings = Settings()
