"""Utility functions for hash calculation and speed formatting."""

import hashlib
from pathlib import Path


def calculate_sha256(file_path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA-256 digest of a file safely using stream processing."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as source:
        while True:
            chunk = source.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


def format_bytes(bytes_num: int) -> str:
    """Format byte count into readable representation."""
    size = float(bytes_num)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"
