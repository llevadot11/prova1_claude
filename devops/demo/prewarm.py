"""Pre-warm cache de explicaciones Claude antes de la demo.

Llama a /explain para los 73 barrios x 24 horas x 4 modos = 7.008 requests.
Rate limit: semaforo de 10 requests concurrentes (~10 req/s con timeout 5s).
Tiempo estimado: ~12 minutos.

Uso:
    python devops/demo/prewarm.py                            # localhost:8000
    python devops/demo/prewarm.py https://ufi-api.railway.app  # Railway
    $env:BASE_URL="https://ufi-api.railway.app"; python devops/demo/prewarm.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

try:
    from tqdm.asyncio import tqdm as async_tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

BASE_URL = (
    sys.argv[1] if len(sys.argv) > 1
    else os.getenv("BASE_URL", "http://localhost:8000")
).rstrip("/")

MODES = ["default", "familiar", "runner", "movilidad_reducida"]
CONCURRENCY = 10
TIMEOUT = 5.0
RETRIES = 2


async def fetch_explain(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    barrio_id: str,
    at: str,
    mode: str,
) -> tuple[bool, str]:
    url = f"{BASE_URL}/explain/{barrio_id}"
    params = {"at": at, "mode": mode}
    async with sem:
        for attempt in range(RETRIES + 1):
            try:
                r = await client.get(url, params=params, timeout=TIMEOUT)
                r.raise_for_status()
                cached = r.json().get("cached", False)
                return True, "HIT" if cached else "MISS"
            except Exception as exc:
                if attempt == RETRIES:
                    return False, f"{barrio_id}@{mode}: {exc}"
                await asyncio.sleep(0.5)
    return False, f"{barrio_id}@{mode}: agotados reintentos"


async def get_barrio_ids(client: httpx.AsyncClient) -> list[str]:
    r = await client.get(f"{BASE_URL}/barrios", timeout=10.0)
    r.raise_for_status()
    return [f["properties"]["barrio_id"] for f in r.json()["features"]]


async def main() -> None:
    print(f"Conectando a {BASE_URL}...")
    async with httpx.AsyncClient() as client:
        try:
            barrio_ids = await get_barrio_ids(client)
        except Exception as exc:
            print(f"[ERROR] No se puede conectar a {BASE_URL}/barrios: {exc}")
            sys.exit(1)

    n_barrios = len(barrio_ids)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    timestamps = [(now + timedelta(hours=h)).isoformat() for h in range(24)]
    tasks = [
        (bid, ts, mode)
        for bid in barrio_ids
        for ts in timestamps
        for mode in MODES
    ]
    total = len(tasks)

    print(f"[OK] {n_barrios} barrios  |  24h  |  {len(MODES)} modos  =  {total} llamadas")
    estimated_s = total / CONCURRENCY
    print(f"     ~{int(estimated_s)}s ({estimated_s/60:.1f} min) con semaforo={CONCURRENCY}\n")

    sem = asyncio.Semaphore(CONCURRENCY)
    errors: list[str] = []
    hits = misses = 0

    async with httpx.AsyncClient() as client:
        coros = [fetch_explain(client, sem, bid, ts, mode) for bid, ts, mode in tasks]
        if HAS_TQDM:
            results = await async_tqdm.gather(*coros, desc="Pre-warming /explain", unit="req")
        else:
            done = 0
            results = []
            for coro in asyncio.as_completed(coros):
                result = await coro
                results.append(result)
                done += 1
                if done % 100 == 0 or done == total:
                    pct = done * 100 // total
                    bar = "=" * (pct // 2) + " " * (50 - pct // 2)
                    print(f"\r[{bar}] {done}/{total}", end="", flush=True)
            print()

    for ok, msg in results:
        if ok:
            if msg == "HIT":
                hits += 1
            else:
                misses += 1
        else:
            errors.append(msg)

    print(f"\n[OK] Cache hits: {hits}  |  Nuevas entradas: {misses}  |  Errores: {len(errors)}")

    if errors:
        log_path = Path(__file__).parent / "prewarm_errors.log"
        log_path.write_text("\n".join(errors), encoding="utf-8")
        print(f"[WARN] {len(errors)} errores -> {log_path}")
    else:
        print("[OK] Pre-warm completado. Cache garantizado para la demo.")


if __name__ == "__main__":
    asyncio.run(main())
