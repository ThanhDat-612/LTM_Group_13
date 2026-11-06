from __future__ import annotations

import os
import threading
from pathlib import Path

from server.duplicate_policy import resolve_duplicate_name
from server.security import SecurityError, safe_upload_path


class PartManager:
    """Manage temporary upload files and reserved final file names.

    The manager guarantees that two clients cannot claim the same final filename
    at the same time, and it keeps temporary `.part` files isolated inside the
    configured upload directory.
    """

    def __init__(self, upload_dir: str | Path, temp_suffix: str = ".part"):
        self.upload_dir = Path(upload_dir).expanduser().resolve()
        self.temp_suffix = temp_suffix
        self._lock = threading.RLock()

    def ensure_directory(self) -> Path:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        return self.upload_dir

    def temp_path_for(self, final_path: str | Path) -> Path:
        path = Path(final_path)
        if not path.is_absolute():
            path = (self.upload_dir / path).resolve(strict=False)
        return path.with_name(f".{path.name}{self.temp_suffix}")

    def reserve_file(self, filename: str, upload_dir: str | Path | None = None) -> Path:
        """Reserve a final filename atomically using a temporary zero-byte file."""
        directory = Path(upload_dir) if upload_dir is not None else self.upload_dir
        directory = directory.expanduser().resolve()

        with self._lock:
            directory.mkdir(parents=True, exist_ok=True)
            if not filename or not isinstance(filename, str):
                raise SecurityError("Tên tệp không hợp lệ")

            safe_name = Path(filename).name
            if not safe_name or safe_name in {".", ".."}:
                raise SecurityError(f"Unsafe filename: {filename!r}")

            candidate = safe_upload_path(directory, safe_name)
            unique_name = resolve_duplicate_name(candidate.name, directory)
            final_path = safe_upload_path(directory, unique_name)

            try:
                with open(final_path, "xb"):
                    pass
                return final_path
            except FileExistsError:
                # The duplicate policy already avoids collisions, but keep the
                # safety net for races across multiple threads/processes.
                recovery = directory / resolve_duplicate_name(final_path.name, directory)
                recovered = safe_upload_path(directory, recovery.name)
                with open(recovered, "xb"):
                    pass
                return recovered

    def commit_upload(self, final_path: str | Path, temp_path: str | Path) -> Path:
        """Move a temp chunk file into place atomically."""
        final = Path(final_path)
        temp = Path(temp_path)

        if not final.is_absolute():
            final = (self.upload_dir / final).resolve(strict=False)
        if not temp.is_absolute():
            temp = (self.upload_dir / temp).resolve(strict=False)

        final.parent.mkdir(parents=True, exist_ok=True)
        safe_upload_path(final.parent, final.name)
        safe_upload_path(temp.parent, temp.name)

        os.replace(temp, final)
        return final

    def cleanup_stale_parts(self, upload_dir: str | Path | None = None) -> int:
        """Remove stale temporary files left behind from interrupted uploads."""
        directory = Path(upload_dir) if upload_dir is not None else self.upload_dir
        directory = directory.expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)

        removed = 0
        for stale in directory.glob(f"*{self.temp_suffix}"):
            try:
                stale.unlink()
                removed += 1
            except OSError:
                continue
        return removed


__all__ = ["PartManager"]
