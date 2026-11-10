"""Temporary part-file lifecycle manager."""

import os
import threading
from pathlib import Path


class PartFileManager:
    """Manages creation and cleanup of temporary upload part files."""

    @staticmethod
    def create_temp_path(destination: Path) -> Path:
        pid = os.getpid()
        tid = threading.get_ident()
        return destination.with_name(f"{destination.name}.{pid}.{tid}.part")

    @staticmethod
    def cleanup(temp_path: Path | None) -> None:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
