import threading
from pathlib import Path

from client.network.upload_queue import UploadQueue
from client.network.upload_worker import CANCELLED_STATUS, UploadWorker


class UploadManager:
    def __init__(self, host, port, callback, max_concurrent=3):
        self.host = host
        self.port = port
        self.callback = callback
        self.queue = UploadQueue(max_concurrent=max_concurrent)
        self.lock = threading.Lock()
        self.workers = {}            # key -> UploadWorker đang chạy
        self._cancel_requested = set()
        self.running = True

    # ---------- Thêm tệp ----------
    def add_files(self, file_paths):
        if not self.running:
            return
        for file_path in file_paths:
            self.queue.enqueue(file_path)
        self._drain()

    def _drain(self):
        """Lấp đầy các slot trống bằng tệp đang chờ. Gọi lại mỗi khi một tệp kết thúc
        (thành công, lỗi hay bị hủy) nên các tệp còn lại luôn được gửi tiếp."""
        if not self.running:
            return
        while True:
            batch = self.queue.next_batch()
            if not batch:
                break
            for file_path in batch:
                worker = UploadWorker(file_path, self.host, self.port, self.callback, self)
                with self.lock:
                    self.workers[file_path] = worker
                    cancel_now = file_path in self._cancel_requested
                    self._cancel_requested.discard(file_path)
                if cancel_now:
                    worker.stop()
                worker.start()

    def mark_done(self, file_path):
        with self.lock:
            self.workers.pop(file_path, None)
        self.queue.mark_done(file_path)
        self._drain()

    # ---------- Hủy ----------
    def cancel(self, file_path):
        """Hủy một tệp: đang chờ thì gỡ khỏi hàng đợi, đang gửi thì dừng worker."""
        if self.queue.remove(file_path):
            self.callback(Path(file_path).name, CANCELLED_STATUS, 0, "0 B/s", "Đã hủy trước khi gửi")
            return True
        with self.lock:
            worker = self.workers.get(file_path)
            if worker is None:
                # tệp vừa rời hàng đợi nhưng worker chưa kịp đăng ký
                self._cancel_requested.add(file_path)
                return False
        worker.stop()
        return True

    def cancel_all(self):
        for file_path in self.queue.clear_pending():
            self.callback(Path(file_path).name, CANCELLED_STATUS, 0, "0 B/s", "Đã hủy trước khi gửi")
        with self.lock:
            workers = list(self.workers.values())
        for worker in workers:
            worker.stop()

    def stop(self):
        self.running = False
        self.cancel_all()