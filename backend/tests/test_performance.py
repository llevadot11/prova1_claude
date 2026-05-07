"""Performance tests — /ufi debe responder en < 100ms con stubs."""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_LIMIT_MS = 100


def _elapsed_ms(url: str) -> tuple[int, float]:
    t0 = time.monotonic()
    r = client.get(url)
    return r.status_code, (time.monotonic() - t0) * 1000


def test_ufi_response_time() -> None:
    # Warm up the in-process cache with one call
    client.get("/ufi")
    # Measure the second call (cache hit path)
    status, ms = _elapsed_ms("/ufi")
    assert status == 200
    assert ms < _LIMIT_MS, f"/ufi took {ms:.1f}ms (limit {_LIMIT_MS}ms)"


def test_ufi_all_modes_response_time() -> None:
    for mode in ("default", "familiar", "runner", "movilidad_reducida"):
        client.get(f"/ufi?mode={mode}")  # warm up
        status, ms = _elapsed_ms(f"/ufi?mode={mode}")
        assert status == 200
        assert ms < _LIMIT_MS, f"/ufi?mode={mode} took {ms:.1f}ms (limit {_LIMIT_MS}ms)"


def test_barrios_geojson_response_time() -> None:
    client.get("/barrios")  # warm up in-memory GeoJSON cache
    status, ms = _elapsed_ms("/barrios")
    assert status == 200
    assert ms < _LIMIT_MS, f"/barrios took {ms:.1f}ms"


def test_modes_response_time() -> None:
    status, ms = _elapsed_ms("/modes")
    assert status == 200
    assert ms < 50, f"/modes took {ms:.1f}ms (limit 50ms)"
