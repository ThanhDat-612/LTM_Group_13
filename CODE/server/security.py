"""Security helpers for the server.

Responsibilities:
- Prevent path traversal.
- Keep uploads inside the configured directory.
- Limit concurrent clients without deadlocking the server.
"""

from __future__ import annotations

import threading
from pathlib import Path


class SecurityError(ValueError):
    """Raised when a security validation fails."""


def is_safe_filename(filename: str) -> bool:
    """Return True only when filename cannot escape the upload directory."""
    if not isinstance(filename, str):
        return False

    value = filename.strip()
    if not value or value != filename:
        return False

    if value in {".", ".."}:
        return False

    if Path(value).is_absolute() or "/" in value or "\\" in value:
        return False

    if any(part in {".", ".."} for part in Path(value).parts):
        return False

    return True


def safe_upload_path(upload_dir: str | Path, filename: str) -> Path:
    """Return a final path guaranteed to remain inside upload_dir."""
    if not is_safe_filename(filename):
        raise SecurityError(f"Unsafe filename: {filename!r}")

    base = Path(upload_dir).expanduser().resolve()
    base.mkdir(parents=True, exist_ok=True)

    destination = (base / filename).resolve(strict=False)
    try:
        destination.relative_to(base)
    except ValueError as exc:
        raise SecurityError("Path traversal detected.") from exc

    if destination.name != filename:
        raise SecurityError(f"Filename resolved unexpectedly: {filename!r}")

    return destination


class ConnectionLimiter:
    """Thread-safe limit for simultaneous client connections/uploads."""

    def __init__(self, max_connections: int = 3):
        if max_connections <= 0:
            raise ValueError("max_connections must be greater than 0")
        self.max_connections = max_connections
        self._semaphore = threading.BoundedSemaphore(max_connections)

    def acquire(self, blocking: bool = True) -> bool:
        return self._semaphore.acquire(blocking=blocking)

    def release(self) -> None:
        try:
            self._semaphore.release()
        except ValueError:
            pass

    def __enter__(self):
        if not self.acquire(blocking=True):
            raise SecurityError("Maximum concurrent connections reached.")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()


def validate_upload_destination(upload_dir: str | Path, filename: str) -> bool:
    """Convenience security check for upload destinations."""
    safe_upload_path(upload_dir, filename)
    return True


__all__ = [
    "SecurityError",
    "ConnectionLimiter",
    "is_safe_filename",
    "safe_upload_path",
    "validate_upload_destination",
]
