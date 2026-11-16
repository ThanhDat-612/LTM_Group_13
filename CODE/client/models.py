from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class FileStatus(Enum):
    WAITING = "waiting"
    SENDING = "sending"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class FileItem:
    path: str
    status: FileStatus = FileStatus.WAITING
    progress: float = 0.0
    error_message: Optional[str] = None

    @classmethod
    def from_upload_update(cls, item_id, status, progress, speed, detail):
        status_text = str(status or "waiting").strip().lower()
        status_map = {
            "waiting": FileStatus.WAITING,
            "pending": FileStatus.WAITING,
            "uploading": FileStatus.SENDING,
            "sending": FileStatus.SENDING,
            "completed": FileStatus.COMPLETED,
            "done": FileStatus.COMPLETED,
            "success": FileStatus.COMPLETED,
            "error": FileStatus.ERROR,
            "failed": FileStatus.ERROR,
            "cancelled": FileStatus.CANCELLED,
            "đã hủy": FileStatus.CANCELLED,
        }
        file_status = status_map.get(status_text, FileStatus.WAITING)
        return cls(
            path=str(item_id),
            status=file_status,
            progress=float(progress or 0),
            error_message=detail if file_status in {FileStatus.ERROR, FileStatus.CANCELLED} else None,
        )

    @property
    def name(self) -> str:
        return Path(self.path).name

    @property
    def size(self) -> int:
        try:
            return Path(self.path).stat().st_size
        except OSError:
            return 0


__all__ = ["FileItem", "FileStatus"]
