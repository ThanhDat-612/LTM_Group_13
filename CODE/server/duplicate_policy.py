"""Duplicate filename handling strategy."""

import time
from pathlib import Path


def generate_unique_path(destination: Path) -> Path:
    """Generate non-conflicting filename using timestamp and increment counter."""
    if not destination.exists():
        return destination

    stem, suffix = destination.stem, destination.suffix
    stamp = time.strftime("%H%M-%d%m%Y")
    candidate = destination.with_name(f"{stem} {stamp}{suffix}")
    counter = 1

    while candidate.exists():
        candidate = destination.with_name(f"{stem} {stamp}-{counter}{suffix}")
        counter += 1

    return candidate
