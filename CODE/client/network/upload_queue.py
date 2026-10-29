import threading
from collections import deque


class UploadQueue:
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.queue = deque()
        self.active = set()
        self.lock = threading.Lock()
        self.done = set()

    def enqueue(self, item):
        with self.lock:
            if item in self.queue or item in self.active:
                return False  # tránh đưa trùng một tệp vào hàng đợi
            self.queue.append(item)
            return True

    def next_batch(self):
        batch = []
        with self.lock:
            while self.queue and len(self.active) < self.max_concurrent:
                item = self.queue.popleft()
                self.active.add(item)
                batch.append(item)
        return batch

    def mark_done(self, item):
        with self.lock:
            self.active.discard(item)
            self.done.add(item)

    def remove(self, item):
        """Gỡ một tệp đang chờ (chưa bắt đầu gửi). Trả về True nếu gỡ được."""
        with self.lock:
            try:
                self.queue.remove(item)
                return True
            except ValueError:
                return False

    def clear_pending(self):
        """Gỡ toàn bộ tệp đang chờ, trả về danh sách các tệp đã gỡ."""
        with self.lock:
            items = list(self.queue)
            self.queue.clear()
            return items