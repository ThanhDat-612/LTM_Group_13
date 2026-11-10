"""Manager for concurrent upload workers."""

import threading
from typing import List, Callable
from client.models import UploadTask, TransferStatus
from client.network.upload_worker import upload_file
from client.network.upload_queue import UploadQueue


class UploadManager:
    def __init__(self, host: str, port: int, max_concurrent: int = 3):
        self.host = host
        self.port = port
        self.max_concurrent = max_concurrent
        self.queue = UploadQueue()
        self.active_workers = 0
        self._lock = threading.Lock()

    def add_file(self, file_path: str):
        import os
        task = UploadTask(
            file_path=file_path,
            file_name=os.path.basename(file_path),
            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0
        )
        self.queue.add_task(task)

    def start_uploads(self, callback: Callable[[UploadTask], None] = None):
        with self._lock:
            while self.active_workers < self.max_concurrent and not self.queue.empty():
                task = self.queue.get_task()
                if task:
                    self.active_workers += 1
                    threading.Thread(target=self._run_worker, args=(task, callback), daemon=True).start()

    def _run_worker(self, task: UploadTask, callback: Callable[[UploadTask], None] = None):
        task.status = TransferStatus.UPLOADING
        try:
            res = upload_file(self.host, self.port, task.file_path)
            if res.get("success"):
                task.status = TransferStatus.COMPLETED
            else:
                task.status = TransferStatus.FAILED
                task.error_message = res.get("message", "Upload failed")
        except Exception as exc:
            task.status = TransferStatus.FAILED
            task.error_message = str(exc)
        finally:
            with self._lock:
                self.active_workers -= 1
            if callback:
                callback(task)
            self.start_uploads(callback)
