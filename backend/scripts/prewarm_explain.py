#!/usr/bin/env python3
"""Pre-warms the explain cache hitting all 73 barrios × 4 modes.

Run this from the backend folder before the demo:
    python scripts/prewarm_explain.py [--base-url http://localhost:8000] [--concurrency 5]

Requires:
  - uvicorn running on BASE_URL
  - ANTHROPIC_API_KEY set (otherwise responses will be fallback templates, cache still warms)
"""
from __future__ import annotations

import argparse
import asyncio
import sys

import httpx

BARRIOS = [f"BAR-{i:03d}" for i in range(1, 74)]
MODES = ["default", "familiar", "runner", "movilidad_reducida"]


async def prewarm(base_url: str, concurrency: int) -> None:
    tasks_total = len(BARRIOS) * len(MODES)
    counts = {"done": 0, "cached": 0, "generated": 0, "errors": 0}
    sem = asyncio.Semaphore(concurrency)

    async def fetch_one(client: httpx.AsyncClient, barrio_id: str, mode: str) -> None:
        async with sem:
            try:
                r = await client.get(
                    f"{base_url}/explain/{barrio_id}",
                    params={"mode": mode},
                    timeout=15.0,
                )
                r.raise_for_status()
                body = r.json()
                counts["done"] += 1
                if body.get("cached"):
                    counts["cached"] += 1
                else:
                    counts["generated"] += 1
                done = counts["done"]
                status = "cached" if body.get("cached") else "new"
                print(
                    f"\r[{done:>3}/{tasks_total}] {barrio_id}/{mode:<20} {status}   ",
                    end="",
                    flush=True,
                )
            except Exception as exc:
                counts["errors"] += 1
                print(f"\nERROR {barrio_id}/{mode}: {exc}", file=sys.stderr)

    async with httpx.AsyncClient() as client:
        # Check server is up
        try:
            await client.get(f"{base_url}/health", timeout=5.0)
        except Exception as exc:
            print(f"Server at {base_url} not reachable: {exc}", file=sys.stderr)
            sys.exit(1)

        all_tasks = [fetch_one(client, bid, m) for bid in BARRIOS for m in MODES]
        await asyncio.gather(*all_tasks)

    print(
        f"\n\nDone: {counts['done']}/{tasks_total} "
        f"(generated={counts['generated']}, cached={counts['cached']}, errors={counts['errors']})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-warm UFI explain cache")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--concurrency", type=int, default=5)
    args = parser.parse_args()
    asyncio.run(prewarm(args.base_url, args.concurrency))


if __name__ == "__main__":
    main()
