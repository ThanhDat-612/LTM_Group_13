from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable, Optional

from common.protocol import recv_json, send_json
from client.network.connection import (
    create_connection,
    close_connection,
)
from client.network.speed_tracker import (
    SpeedSnapshot,
    SpeedTracker,
)
from client.network.upload_queue import UploadJob


ProgressCallback = Callable[[SpeedSnapshot], None]


class UploadProtocolError(RuntimeError):
    pass


class UploadWorker:
    def __init__(
        self,
        host: str,
        port: int,
        *,
        chunk_size: int = 1024 * 1024,
        timeout: float = 30.0,
        tracker: Optional[SpeedTracker] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        if not 1 <= int(port) <= 65535:
            raise ValueError(
                "port must be between 1 and 65535"
            )

        if chunk_size <= 0 or chunk_size > 4 * 1024 * 1024:
            raise ValueError(
                "chunk_size must be between 1 byte and 4 MiB"
            )

        self.host = host
        self.port = int(port)
        self.chunk_size = int(chunk_size)
        self.timeout = timeout
        self.tracker = tracker or SpeedTracker()
        self.progress_callback = progress_callback

    def upload(self, job: UploadJob) -> dict:
        path = Path(job.file_path)

        if not path.is_file():
            raise FileNotFoundError(path)

        total = path.stat().st_size
        file_id = job.job_id

        self.tracker.start(file_id, total)

        sock = None
        sent = 0
        digest = hashlib.sha256()

        try:
            sock = create_connection(
                self.host,
                self.port,
                timeout=self.timeout,
            )
            sock.settimeout(self.timeout)

            send_json(sock, {
                "type": "UPLOAD_REQUEST",
                "filename": path.name,
                "size": total,
            })

            ack = recv_json(sock)

            if ack.get("type") == "UPLOAD_ERROR":
                raise UploadProtocolError(
                    ack.get("message", "Server rejected upload")
                )

            if (
                ack.get("type") != "UPLOAD_ACK"
                or ack.get("status") != "accepted"
            ):
                raise UploadProtocolError(
                    f"Unexpected upload acknowledgement: {ack}"
                )

            # 3. Send each JSON header followed by raw chunk bytes.
            with path.open("rb") as source:
                while True:
                    chunk = source.read(self.chunk_size)

                    if not chunk:
                        break

                    send_json(sock, {
                        "type": "FILE_DATA",
                        "size": len(chunk),
                    })

                    sock.sendall(chunk)
                    digest.update(chunk)
                    sent += len(chunk)

                    snapshot = self.tracker.update(
                        file_id, sent
                    )

                    if self.progress_callback:
                        self.progress_callback(snapshot)

            # 4. Tell the server that no more chunks will follow.
            send_json(sock, {"type": "UPLOAD_DONE"})
            print("[DEBUG] Da gui UPLOAD_DONE, dang cho server tra ket qua...")

            result = recv_json(sock)
            print(f"[DEBUG] Server tra ve: {result}")
            if result.get("type") != "UPLOAD_RESULT":
                raise UploadProtocolError(
                    f"Unexpected upload result: {result}"
                )

            if result.get("status") != "success":
                raise UploadProtocolError(
                    result.get("message", "Upload failed")
                )

            snapshot = self.tracker.finish(file_id)

            if self.progress_callback:
                self.progress_callback(snapshot)

            return {
                "file_id": file_id,
                "filename": path.name,
                "final_name": result.get(
                    "final_name", path.name
                ),
                "bytes_sent": sent,
                "total_bytes": total,
                "sha256": digest.hexdigest(),
                "status": "completed",
            }

        finally:
            if sock is not None:
                close_connection(sock)
