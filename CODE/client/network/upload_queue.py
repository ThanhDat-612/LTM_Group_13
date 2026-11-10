"""Client Upload Queue Manager."""

import queue
from client.models import UploadTask


class UploadQueue:
    def __init__(self):
        self._queue = queue.Queue()

    def add_task(self, task: UploadTask):
        self._queue.put(task)

    def get_task(self) -> UploadTask | None:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def empty(self) -> bool:
        return self._queue.empty()
