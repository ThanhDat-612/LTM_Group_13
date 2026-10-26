"""
Security helpers for the server.

Responsibilities:
- Prevent path traversal.
- Keep uploaded files inside the configured upload directory.
- Limit concurrent clients.
"""

from __future__ import annotations

import threading
from pathlib import Path


class SecurityError(ValueError):
    """Raised when a security validation fails."""


def is_safe_filename(filename: str) -> bool:
    """Return True only when filename cannot escape the upload directory."""
    if not isinstance(filename, str) or not filename.strip():
        return False

    path = Path(filename)

    if path.is_absolute():
        return False

    if "/" in filename or "\\" in filename:
        return False

    if filename in {".", ".."} or ".." in filename:
        return False

    return True


def safe_upload_path(upload_dir: str | Path, filename: str) -> Path:
    """
    Build a safe destination path and verify it stays inside upload_dir.

    Raises SecurityError for path traversal or invalid filenames.
    """
    if not is_safe_filename(filename):
        raise SecurityError(f"Unsafe filename: {filename!r}")

    base = Path(upload_dir).resolve()
    base.mkdir(parents=True, exist_ok=True)

    destination = (base / filename).resolve()

    try:
        destination.relative_to(base)
    except ValueError as exc:
        raise SecurityError("Path traversal detected.") from exc

    return destination


class ConnectionLimiter:
    """Thread-safe limit for simultaneous client connections/uploads."""

    def __init__(self, max_connections: int = 3):
        if max_connections <= 0:
            raise ValueError("max_connections must be greater than 0")

        self.max_connections = max_connections
        self._semaphore = threading.BoundedSemaphore(max_connections)

    def acquire(self, blocking: bool = False) -> bool:
        return self._semaphore.acquire(blocking=blocking)

    def release(self) -> None:
        try:
            self._semaphore.release()
        except ValueError:
            # Avoid crashing the server if release is accidentally called twice.
            pass

    def __enter__(self):
        if not self.acquire():
            raise SecurityError("Maximum concurrent connections reached.")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()


def validate_upload_destination(upload_dir: str | Path, filename: str) -> bool:
    """Convenience security check for upload destinations."""
    safe_upload_path(upload_dir, filename)
    return True
