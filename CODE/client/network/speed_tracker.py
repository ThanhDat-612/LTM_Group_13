from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Optional


@dataclass(frozen=True)
class SpeedSnapshot:
    file_id: str
    bytes_sent: int
    total_bytes: int
    percent: float
    bytes_per_second: float
    elapsed_seconds: float
    complete: bool


class SpeedTracker:
    def __init__(
        self,
        smoothing_window_seconds: float = 0.5
    ) -> None:
        self._lock = Lock()
        self._window = max(
            0.1, smoothing_window_seconds
        )
        self._items: dict[str, dict] = {}

    def start(self, file_id: str, total_bytes: int) -> None:
        with self._lock:
            now = monotonic()

            self._items[file_id] = {
                "total": max(0, int(total_bytes)),
                "sent": 0,
                "started": now,
                "last_time": now,
                "last_bytes": 0,
                "speed": 0.0,
                "complete": False,
            }

    def update(
        self,
        file_id: str,
        bytes_sent: int
    ) -> SpeedSnapshot:
        """Update using cumulative bytes sent."""
        with self._lock:
            if file_id not in self._items:
                raise KeyError(
                    f"Tracker not started for {file_id!r}"
                )

            item = self._items[file_id]
            now = monotonic()

            sent = max(
                item["sent"],
                min(int(bytes_sent), item["total"])
            )

            dt = now - item["last_time"]

            if dt >= self._window:
                item["speed"] = (
                    max(0, sent - item["last_bytes"]) / dt
                )
                item["last_time"] = now
                item["last_bytes"] = sent

            item["sent"] = sent
            item["complete"] = sent >= item["total"]

            return self._snapshot(file_id, item, now)

    def finish(self, file_id: str) -> SpeedSnapshot:
        with self._lock:
            if file_id not in self._items:
                raise KeyError(
                    f"Tracker not started for {file_id!r}"
                )

            item = self._items[file_id]
            now = monotonic()

            item["sent"] = item["total"]
            item["complete"] = True

            elapsed = max(
                now - item["started"], 0.001
            )

            item["speed"] = item["total"] / elapsed

            return self._snapshot(file_id, item, now)

    def get(
        self,
        file_id: str
    ) -> Optional[SpeedSnapshot]:
        with self._lock:
            item = self._items.get(file_id)

            if item is None:
                return None

            return self._snapshot(
                file_id, item, monotonic()
            )

    def remove(self, file_id: str) -> None:
        with self._lock:
            self._items.pop(file_id, None)

    @staticmethod
    def _snapshot(
        file_id: str,
        item: dict,
        now: float
    ) -> SpeedSnapshot:
        total = item["total"]
        sent = item["sent"]

        percent = (
            100.0
            if total == 0
            else min(100.0, sent * 100.0 / total)
        )

        return SpeedSnapshot(
            file_id=file_id,
            bytes_sent=sent,
            total_bytes=total,
            percent=percent,
            bytes_per_second=item["speed"],
            elapsed_seconds=max(
                0.0, now - item["started"]
            ),
            complete=item["complete"],
        )
