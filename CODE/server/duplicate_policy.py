from __future__ import annotations

from datetime import datetime
from pathlib import Path


def resolve_duplicate_name(filename: str, target_dir: str | Path) -> str:
    directory = Path(target_dir)
    directory.mkdir(parents=True, exist_ok=True)

    original = Path(filename)
    name = original.name
    stem = original.stem
    suffix = original.suffix

    candidate = directory / name
    if not candidate.exists():
        return name

    now = datetime.now()
    stamp = now.strftime("%d%m%Y_%H%M%S")
    unique_name = f"{stem}_{stamp}{suffix}"
    final = directory / unique_name
    counter = 1
    while final.exists():
        unique_name = f"{stem}_{stamp}_{counter}{suffix}"
        final = directory / unique_name
        counter += 1
    return final.name
