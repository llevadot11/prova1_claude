"""Shared pytest fixtures."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import PropertyMock, patch

import duckdb
import pytest

# Timestamp used in mini.parquet — 2026-05-07 10:00:00 UTC
FIXTURE_TS = datetime(2026, 5, 7, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="session")
def mini_parquet(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Creates a minimal valid ufi_latest.parquet with 5 barrios × 1 hour."""
    p = tmp_path_factory.mktemp("fixtures") / "mini.parquet"
    con = duckdb.connect()
    con.execute(
        """
        CREATE TABLE mini AS
        SELECT
            col0  AS barrio_id,
            col1::TIMESTAMP AS timestamp,
            col2  AS ufi_default,
            col3  AS score_trafico,
            col4  AS score_accidentes,
            col5  AS score_aire,
            col6  AS score_meteo,
            col7  AS score_sensibilidad
        FROM (VALUES
            ('BAR-001', '2026-05-07 10:00:00', 45.0, 0.60, 0.50, 0.40, 0.30, 0.20),
            ('BAR-002', '2026-05-07 10:00:00', 30.0, 0.30, 0.40, 0.20, 0.50, 0.10),
            ('BAR-003', '2026-05-07 10:00:00', 60.0, 0.70, 0.60, 0.50, 0.40, 0.30),
            ('BAR-004', '2026-05-07 10:00:00', 20.0, 0.20, 0.15, 0.10, 0.25, 0.05),
            ('BAR-005', '2026-05-07 10:00:00', 75.0, 0.80, 0.75, 0.70, 0.65, 0.60)
        ) t(col0, col1, col2, col3, col4, col5, col6, col7)
        """
    )
    con.execute(f"COPY mini TO '{p}' (FORMAT PARQUET)")
    con.close()
    return p
