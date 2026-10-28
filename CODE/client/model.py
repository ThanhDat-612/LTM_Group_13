
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class FileStatus(Enum):
    WAITING = "waiting"
    SENDING = "sending"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class FileItem:
    path: str
    status: FileStatus = FileStatus.WAITING
    progress: float = 0.0
    error_message: Optional[str] = None

    @property
    def name(self) -> str:
        return Path(self.path).name

    @property
    def size(self) -> int:
        try:
            return Path(self.path).stat().st_size
        except OSError:
            return 0
