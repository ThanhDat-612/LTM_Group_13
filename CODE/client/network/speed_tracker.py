import time


class SpeedTracker:
    def __init__(self):
        self.start_time = None
        self.last_time = None
        self.last_bytes = 0

    def start(self):
        self.start_time = time.monotonic()
        self.last_time = self.start_time
        self.last_bytes = 0

    def update(self, current_bytes):
        now = time.monotonic()
        elapsed = now - self.last_time
        if elapsed <= 0:
            return 0
        speed = (current_bytes - self.last_bytes) / elapsed
        self.last_time = now
        self.last_bytes = current_bytes
        return max(speed, 0)

    def total_speed(self, total_bytes):
        elapsed = max(time.monotonic() - self.start_time, 0.1)
        return total_bytes / elapsed if self.start_time else 0
