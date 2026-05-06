"""QA cruzado rapido: bate todos los endpoints y reporta estado.

Uso:
    python devops/demo/qa_check.py                            # localhost:8000
    python devops/demo/qa_check.py https://ufi-api.railway.app
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")

PASS = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def _encode_at(ts: str) -> str:
    return urllib.parse.quote(ts, safe="")


def get(path: str, timeout: int = 8) -> tuple[int, dict | None]:
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=timeout) as r:
            body = r.read()
            try:
                return r.status, json.loads(body)
            except Exception:
                return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return 0, {"error": str(e)}


def check(label: str, status: int, body: dict | None, assertion=None) -> bool:
    ok = 200 <= status < 300
    if ok and assertion:
        try:
            ok = assertion(body)
        except Exception:
            ok = False
    icon = PASS if ok else FAIL
    detail = ""
    if not ok and body:
        detail = f"  -> {body}"
    print(f"{icon} [{status}] {label}{detail}")
    return ok


def main() -> None:
    now_dt = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    now = now_dt.isoformat()
    now_enc = _encode_at(now)
    print(f"\nQA Check -> {BASE}")
    print(f"   Timestamp: {now}\n")

    failures = 0

    # /health
    s, b = get("/health")
    ok = check("/health", s, b, lambda d: d.get("api") == "ok")
    if not ok:
        failures += 1
    if b:
        for k, v in b.items():
            icon = PASS if v == "ok" else (WARN if v == "unknown" else FAIL)
            print(f"   {icon} {k}: {v}")

    # /modes
    s, b = get("/modes")
    ok = check("/modes", s, b, lambda d: isinstance(d, list) and len(d) == 4)
    if not ok:
        failures += 1

    # /barrios
    s, b = get("/barrios")
    n_barrios = len(b.get("features", [])) if b else 0
    ok = check(f"/barrios  ({n_barrios} features)", s, b,
               lambda d: d.get("type") == "FeatureCollection" and len(d.get("features", [])) > 0)
    if not ok:
        failures += 1

    # /tramos
    s, b = get("/tramos")
    n_tramos = len(b.get("features", [])) if b else 0
    ok = check(f"/tramos  ({n_tramos} features)", s, b,
               lambda d: d.get("type") == "FeatureCollection")
    if not ok:
        failures += 1

    # /ufi?mode=default
    s, b = get(f"/ufi?at={now_enc}&mode=default")
    n_ufi = len(b.get("barrios", [])) if b else 0
    ok = check(f"/ufi?mode=default  ({n_ufi} barrios)", s, b,
               lambda d: len(d.get("barrios", [])) > 0)
    if not ok:
        failures += 1

    # /ufi todos los modos
    for mode in ("familiar", "runner", "movilidad_reducida"):
        s, b = get(f"/ufi?at={now_enc}&mode={mode}")
        ok = check(f"/ufi?mode={mode}", s, b, lambda d: len(d.get("barrios", [])) > 0)
        if not ok:
            failures += 1

    # /tramos/state
    s, b = get(f"/tramos/state?at={now_enc}")
    n_tr = len(b.get("tramos", [])) if b else 0
    ok = check(f"/tramos/state  ({n_tr} tramos)", s, b,
               lambda d: len(d.get("tramos", [])) > 0)
    if not ok:
        failures += 1

    # /barrio/{id} con el primer barrio
    if n_barrios > 0:
        _, barrios_body = get("/barrios")
        first_id = barrios_body["features"][0]["properties"]["barrio_id"]
        s, b = get(f"/barrio/{first_id}?at={now_enc}&mode=default")
        ok = check(f"/barrio/{first_id}", s, b, lambda d: "ufi" in d)
        if not ok:
            failures += 1

        # /explain/{id} — puede tardar, unico con Claude
        print(f"\n   (probando /explain/{first_id} -- puede tardar 3-5s si no cacheado)")
        s, b = get(f"/explain/{first_id}?at={now_enc}&mode=default", timeout=15)
        cached = b.get("cached", False) if b else False
        ok = check(f"/explain/{first_id}  (cached={cached})", s, b,
                   lambda d: bool(d.get("text")))
        if not ok:
            failures += 1

    # /docs (Swagger UI) — responde HTML, solo comprobamos status
    s, _ = get("/docs")
    ok = 200 <= s < 300
    icon = PASS if ok else FAIL
    print(f"{icon} [{s}] /docs  (Swagger UI)")
    if not ok:
        failures += 1

    print(f"\n{'=' * 50}")
    if failures == 0:
        print(f"{PASS} Todos los endpoints OK. La API esta lista.")
    else:
        print(f"{FAIL} {failures} endpoint(s) fallaron. Revisar antes del deploy.")
    print()


if __name__ == "__main__":
    main()
