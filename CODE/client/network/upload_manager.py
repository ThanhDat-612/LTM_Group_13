from __future__ import annotations

from concurrent.futures import (
    ThreadPoolExecutor,
    wait,
    FIRST_COMPLETED,
)
from threading import Lock
from typing import Callable, Optional

from client.network.upload_queue import (
    UploadJob,
    UploadQueue,
)
from client.network.upload_worker import UploadWorker


class UploadManager:
    def __init__(
        self,
        worker_factory: Callable[[], UploadWorker],
        *,
        max_concurrent: int = 2,
        upload_queue: Optional[UploadQueue] = None,
    ) -> None:
        if max_concurrent < 1:
            raise ValueError(
                "max_concurrent must be at least 1"
            )

        self.queue = upload_queue or UploadQueue()
        self.worker_factory = worker_factory
        self.max_concurrent = max_concurrent

        self._lock = Lock()
        self._cancelled = False

    def add_file(
        self,
        file_path: str,
        job_id: Optional[str] = None
    ) -> UploadJob:
        return self.queue.add(file_path, job_id)

    def remove_waiting(self, job_id: str) -> bool:
        return self.queue.remove(job_id)

    def pending(self) -> list[UploadJob]:
        return self.queue.snapshot()

    def cancel_pending_run(self) -> None:
        """Stop scheduling queued files; running uploads finish."""
        with self._lock:
            self._cancelled = True

    def run(self) -> list[dict]:
        with self._lock:
            self._cancelled = False

        results: list[dict] = []
        active = {}

        with ThreadPoolExecutor(
            max_workers=self.max_concurrent
        ) as executor:

            while (
                active
                or (
                    not self._is_cancelled()
                    and not self.queue.empty()
                )
            ):
                # Fill available worker slots.
                while (
                    not self._is_cancelled()
                    and len(active) < self.max_concurrent
                ):
                    job = self.queue.get(block=False)

                    if job is None:
                        break

                    print(f"[CHO UPLOAD] {job.name}")

                    future = executor.submit(
                        self._upload_one, job
                    )
                    active[future] = job

                    print(f"[DANG UPLOAD] {job.name}")
                    print(f"[SO TAI TAC] {len(active)}/{self.max_concurrent}")

                if not active:
                    break

                done, _ = wait(
                    active,
                    return_when=FIRST_COMPLETED,
                )

                for future in done:
                    job = active.pop(future)

                    try:
                        result = future.result()
                        results.append(result)
                        print(f"[HOAN TAT] {job.name}: {result.get('status')}")

                    except Exception as exc:
                        results.append({
                            "file_id": job.job_id,
                            "filename": job.name,
                            "status": "failed",
                            "error": str(exc),
                        })

                    finally:
                        self.queue.task_done(job)

        return results

    def _is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def _upload_one(self, job: UploadJob) -> dict:
        worker = self.worker_factory()
        return worker.upload(job)
