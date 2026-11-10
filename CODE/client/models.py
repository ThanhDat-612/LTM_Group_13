"""Client Task and File Models."""

from dataclasses import dataclass, field
from enum import Enum


class TransferStatus(Enum):
    PENDING = "PENDING"
    UPLOADING = "UPLOADING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class UploadTask:
    file_path: str
    file_name: str
    file_size: int
    status: TransferStatus = TransferStatus.PENDING
    progress: float = 0.0
    speed: str = "0 B/s"
    error_message: str = ""
