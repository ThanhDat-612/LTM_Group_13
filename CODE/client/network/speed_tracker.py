"""Transfer Speed & Progress Tracker."""

import time


class SpeedTracker:
    def __init__(self):
        self.start_time = time.time()
        self.bytes_transferred = 0

    def update(self, chunk_bytes: int) -> tuple[float, str]:
        self.bytes_transferred += chunk_bytes
        elapsed = time.time() - self.start_time
        speed_bps = self.bytes_transferred / elapsed if elapsed > 0 else 0

        if speed_bps < 1024:
            speed_str = f"{speed_bps:.1f} B/s"
        elif speed_bps < 1024 * 1024:
            speed_str = f"{speed_bps / 1024:.1f} KB/s"
        else:
            speed_str = f"{speed_bps / (1024 * 1024):.1f} MB/s"

        return speed_bps, speed_str
