from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["api"] == "ok"



def test_modes():
    r = client.get("/modes")
    assert r.status_code == 200
    ids = {m["id"] for m in r.json()}
    assert ids == {"default", "familiar", "runner", "movilidad_reducida"}


def test_ufi_default():
    r = client.get("/ufi")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "default"
    assert len(body["barrios"]) == 73
    sample = body["barrios"][0]
    assert 0 <= sample["ufi"] <= 100
    assert {c["family"] for c in sample["contribuciones"]} == {
        "trafico", "accidentes", "aire", "meteo", "sensibilidad"
    }


def test_barrio_detail_not_found():
    r = client.get("/barrio/NOPE-999")
    assert r.status_code == 404


def test_barrio_detail_ok():
    r = client.get("/barrio/BAR-001")
    assert r.status_code == 200
    body = r.json()
    assert body["barrio_id"] == "BAR-001"
    assert "raw" in body


def test_tramos_state():
    r = client.get("/tramos/state")
    assert r.status_code == 200
    body = r.json()
    assert len(body["tramos"]) == 530
    assert all(1 <= t["state"] <= 6 for t in body["tramos"])


def test_explain_fallback_offline():
    r = client.get("/explain/BAR-001")
    assert r.status_code == 200
    body = r.json()
    assert body["barrio_id"] == "BAR-001"
    assert isinstance(body["text"], str) and len(body["text"]) > 0
