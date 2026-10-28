from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue, Empty
from threading import Lock
from time import time
from typing import Optional


@dataclass
class UploadJob:
    file_path: str
    job_id: str = ""
    added_at: float = field(default_factory=time)

    def __post_init__(self) -> None:
        self.file_path = str(
            Path(self.file_path).expanduser().resolve()
        )
        if not self.job_id:
            self.job_id = self.file_path

    @property
    def name(self) -> str:
        return Path(self.file_path).name


class UploadQueue:
    """FIFO queue supporting add, get, remove and snapshots."""

    def __init__(self) -> None:
        self._queue: Queue[UploadJob] = Queue()
        self._lock = Lock()
        self._pending_ids: set[str] = set()

    def add(
        self,
        file_path: str,
        job_id: Optional[str] = None
    ) -> UploadJob:
        path = Path(file_path).expanduser().resolve()

        if not path.is_file():
            raise FileNotFoundError(
                f"File does not exist: {path}"
            )

        job = UploadJob(
            str(path),
            job_id or str(path)
        )

        with self._lock:
            if job.job_id in self._pending_ids:
                raise ValueError(
                    f"File is already waiting: {job.name}"
                )

            self._pending_ids.add(job.job_id)
            self._queue.put(job)

        return job

    def get(
        self,
        block: bool = True,
        timeout: Optional[float] = None
    ) -> Optional[UploadJob]:
        try:
            return self._queue.get(
                block=block,
                timeout=timeout
            )
        except Empty:
            return None

    def task_done(self, job: UploadJob) -> None:
        with self._lock:
            self._pending_ids.discard(job.job_id)

        self._queue.task_done()

    def remove(self, job_id: str) -> bool:
        """Remove a waiting job by ID."""
        with self._lock:
            items: list[UploadJob] = []
            removed = False

            while True:
                try:
                    item = self._queue.get_nowait()
                except Empty:
                    break

                if not removed and item.job_id == job_id:
                    removed = True
                    self._pending_ids.discard(item.job_id)
                else:
                    items.append(item)

                self._queue.task_done()

            for item in items:
                self._queue.put(item)

            return removed

    def snapshot(self) -> list[UploadJob]:
        """Return waiting jobs without removing them."""
        with self._lock:
            items: list[UploadJob] = []

            while True:
                try:
                    item = self._queue.get_nowait()
                except Empty:
                    break

                items.append(item)
                self._queue.task_done()

            for item in items:
                self._queue.put(item)

            return list(items)

    def __len__(self) -> int:
        return self._queue.qsize()

    def empty(self) -> bool:
        return self._queue.empty()
