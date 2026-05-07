"""Tests de la rama DuckDB de store.py usando el fixture mini.parquet (P7)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import PropertyMock, patch

import pytest

from tests.conftest import FIXTURE_TS


def test_load_ufi_from_parquet_returns_real_data(mini_parquet: Path) -> None:
    from app import store
    from app.config import Settings

    with patch.object(Settings, "ufi_parquet", new_callable=PropertyMock, return_value=mini_parquet):
        # Invalidate cache so we don't get stub results from a previous test run
        store._ufi_cache.clear()
        barrios = store.load_ufi(FIXTURE_TS, "default")

    assert len(barrios) == 5
    ids = {b.barrio_id for b in barrios}
    assert "BAR-001" in ids
    assert "BAR-005" in ids
    for b in barrios:
        assert 0 <= b.ufi <= 100
        assert len(b.contribuciones) == 5


def test_load_ufi_applies_mode_weights(mini_parquet: Path) -> None:
    from app import store
    from app.config import Settings

    with patch.object(Settings, "ufi_parquet", new_callable=PropertyMock, return_value=mini_parquet):
        store._ufi_cache.clear()
        default = store.load_ufi(FIXTURE_TS, "default")
        runner = store.load_ufi(FIXTURE_TS, "runner")

    # Runner gives much more weight to aire (0.40) vs default (0.20)
    # BAR-003 has score_aire=0.50, score_trafico=0.70
    b_default = next(b for b in default if b.barrio_id == "BAR-003")
    b_runner = next(b for b in runner if b.barrio_id == "BAR-003")
    # UFI values should differ because weights differ
    assert b_default.ufi != b_runner.ufi


def test_validate_parquet_schema_ok(mini_parquet: Path) -> None:
    from app import store
    from app.config import Settings

    with patch.object(Settings, "ufi_parquet", new_callable=PropertyMock, return_value=mini_parquet):
        missing = store.validate_parquet_schema()

    assert missing == [], f"Unexpected missing columns: {missing}"


def test_validate_parquet_schema_no_file() -> None:
    from app import store
    from app.config import Settings
    from pathlib import Path

    with patch.object(
        Settings, "ufi_parquet", new_callable=PropertyMock,
        return_value=Path("/nonexistent/path/ufi.parquet")
    ):
        missing = store.validate_parquet_schema()

    assert missing == []  # No file → no error, empty list


def test_ufi_ttl_cache_hit(mini_parquet: Path) -> None:
    from app import store
    from app.config import Settings

    with patch.object(Settings, "ufi_parquet", new_callable=PropertyMock, return_value=mini_parquet):
        store._ufi_cache.clear()
        first = store.load_ufi(FIXTURE_TS, "default")
        second = store.load_ufi(FIXTURE_TS, "default")

    # Should be the same list object (cache hit returns the cached reference)
    assert first is second


def test_load_ufi_fallback_stub_when_no_parquet() -> None:
    from app import store
    from app.config import Settings
    from pathlib import Path

    with patch.object(
        Settings, "ufi_parquet", new_callable=PropertyMock,
        return_value=Path("/nonexistent/ufi.parquet")
    ):
        store._ufi_cache.clear()
        barrios = store.load_ufi(FIXTURE_TS, "default")

    assert len(barrios) == 73  # full stub
    assert all(0 <= b.ufi <= 100 for b in barrios)
