"""Genera snapshot de fallback. Lanzar el sábado a las 22:00.

Copia el ufi_latest.parquet actual a un nombre datado y deja
un alias `demo_snapshot.parquet` que el API leerá si DEMO_OFFLINE=1.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "data" / "processed" / "ufi_latest.parquet"
SNAPSHOTS_DIR = REPO_ROOT / "demo" / "snapshots"
ALIAS = REPO_ROOT / "data" / "processed" / "demo_snapshot.parquet"


def main() -> None:
    if not SRC.exists():
        raise FileNotFoundError(f"No existe {SRC}. Lanza primero `python -m packages.ml.score`.")
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    target = SNAPSHOTS_DIR / f"ufi_{stamp}.parquet"
    shutil.copy(SRC, target)
    shutil.copy(SRC, ALIAS)
    print(f"✅ Snapshot dejado en {target} (+ alias {ALIAS.name})")


if __name__ == "__main__":
    main()
