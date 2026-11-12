import socket
import threading
import time
from pathlib import Path

from common.constants import CHUNK_SIZE, FILE_STATUS_COMPLETED, FILE_STATUS_ERROR, FILE_STATUS_UPLOADING
from common.protocol import pack_json, recv_json, send_json
from common.utils import format_speed

CANCELLED_STATUS = "đã hủy"   # từ "hủy" được giao diện nhận diện để đổi màu

CONNECT_TIMEOUT = 10      # giây, cho kết nối và gửi/nhận thông thường
RESULT_TIMEOUT = 120      # giây, chờ server ghi xong tệp sau UPLOAD_DONE
EMIT_INTERVAL = 0.1       # giây, giới hạn tần suất cập nhật giao diện


class UploadCancelled(Exception):
    pass


class UploadWorker(threading.Thread):
    def __init__(self, file_path, host, port, callback, queue_controller):
        super().__init__(daemon=True)
        self.key = file_path              # đúng giá trị đã enqueue -> mark_done khớp với hàng đợi
        self.file_path = Path(file_path)
        self.host = host
        self.port = port
        self.callback = callback
        self.queue_controller = queue_controller
        self._stop_event = threading.Event()
        self._sock = None

    def stop(self):
        """Hủy upload: đặt cờ và đóng socket để thoát cả khi đang chờ server trả lời."""
        self._stop_event.set()
        sock = self._sock
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def _emit(self, status, progress, speed, detail):
        self.callback(self.file_path.name, status, progress, speed, detail)

    def _check_cancel(self):
        if self._stop_event.is_set():
            raise UploadCancelled()

    def run(self):
        progress = 0
        try:
            if not self.file_path.is_file():
                self._emit(FILE_STATUS_ERROR, 0, "0 B/s", "Tệp không tồn tại")
                return

            self._check_cancel()
            self._emit(FILE_STATUS_UPLOADING, 0, "0 B/s", "Đang gửi")
            total = self.file_path.stat().st_size

            with socket.create_connection((self.host, int(self.port)), timeout=CONNECT_TIMEOUT) as sock:
                self._sock = sock
                self._check_cancel()
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                send_json(sock, {
                    "type": "UPLOAD_REQUEST",
                    "filename": self.file_path.name,
                    "size": total,
                })
                ack = recv_json(sock)
                if not ack:
                    raise RuntimeError("Server không phản hồi hợp lệ")
                if ack.get("type") == "UPLOAD_ERROR":
                    raise RuntimeError(ack.get("message", "Server từ chối upload"))

                sent = 0
                start = time.monotonic()
                last_emit = 0.0
                with open(self.file_path, "rb") as fh:
                    while True:
                        self._check_cancel()
                        chunk = fh.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        sock.sendall(pack_json({"type": "FILE_DATA", "size": len(chunk)}) + chunk)
                        sent += len(chunk)

                        now = time.monotonic()
                        if now - last_emit >= EMIT_INTERVAL:
                            last_emit = now
                            progress = min(int(sent / total * 100), 99) if total else 99
                            speed = sent / max(now - start, 0.1)
                            self._emit(FILE_STATUS_UPLOADING, progress, format_speed(speed), "Đang gửi")

                if sent != total:
                    raise RuntimeError("Dung lượng tệp thay đổi trong lúc gửi")

                self._check_cancel()
                send_json(sock, {"type": "UPLOAD_DONE"})
                sock.settimeout(RESULT_TIMEOUT)
                result = recv_json(sock)
                if result.get("status") == "success":
                    self._emit(FILE_STATUS_COMPLETED, 100, "0 B/s", "Hoàn tất")
                else:
                    raise RuntimeError(result.get("message", "Upload thất bại"))

        except Exception as exc:
            # Lỗi socket do chính mình đóng khi hủy cũng được coi là "đã hủy"
            if isinstance(exc, UploadCancelled) or self._stop_event.is_set():
                self._emit(CANCELLED_STATUS, progress, "0 B/s", "Đã hủy upload")
            elif isinstance(exc, EOFError):
                self._emit(FILE_STATUS_ERROR, progress, "0 B/s", "Server đã đóng kết nối giữa chừng")
            elif isinstance(exc, socket.timeout):
                self._emit(FILE_STATUS_ERROR, progress, "0 B/s", "Server không phản hồi (quá thời gian chờ)")
            elif isinstance(exc, ConnectionRefusedError):
                self._emit(FILE_STATUS_ERROR, progress, "0 B/s", "Server từ chối kết nối")
            else:
                self._emit(FILE_STATUS_ERROR, progress, "0 B/s", str(exc))
        finally:
            # Luôn giải phóng slot để tệp kế tiếp trong hàng đợi được gửi, dù tệp này lỗi hay bị hủy
            self.queue_controller.mark_done(self.key)