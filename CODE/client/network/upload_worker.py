import socket
import threading
import time
from pathlib import Path

from client.network.connection import load_runtime_config
from common.constants import FILE_STATUS_COMPLETED, FILE_STATUS_ERROR, FILE_STATUS_UPLOADING
from common.protocol import pack_json, recv_json, send_json
from common.utils import format_speed

RUNTIME_CONFIG = load_runtime_config()
CHUNK_SIZE = int(RUNTIME_CONFIG.get("chunk_size", 65536))
CONNECT_TIMEOUT = int(RUNTIME_CONFIG.get("timeout_seconds", 30))
RESULT_TIMEOUT = max(int(RUNTIME_CONFIG.get("timeout_seconds", 30)), 10)

CANCELLED_STATUS = "đã hủy"   # từ "hủy" được giao diện nhận diện để đổi màu
EMIT_INTERVAL = 0.1            # giây, giới hạn tần suất cập nhật giao diện


class UploadCancelled(Exception):
    pass


class UploadRemoteClosed(Exception):
    """Raised when the server or network closes the upload socket unexpectedly."""


class UploadWorker(threading.Thread):
    def __init__(self, file_path, host, port, callback, queue_controller, session_id=None):
        super().__init__(daemon=True)
        self.key = str(file_path)             # khóa ổn định để đồng bộ với hàng đợi và giao diện
        self.file_path = Path(file_path)
        self.host = host
        self.port = port
        self.callback = callback
        self.queue_controller = queue_controller
        self.session_id = session_id
        self._stop_event = threading.Event()
        self._sock = None
        self._retried = False

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
        self.callback(self.key, status, progress, speed, detail)

    def _check_cancel(self):
        if self._stop_event.is_set():
            raise UploadCancelled("Upload was cancelled by the user")

    @staticmethod
    def _classify_exception(exc, stop_event_set):
        if isinstance(exc, UploadCancelled) or stop_event_set:
            return CANCELLED_STATUS, "Đã hủy upload"

        if isinstance(exc, (EOFError, ConnectionResetError, BrokenPipeError, ConnectionAbortedError, UploadRemoteClosed)):
            return FILE_STATUS_ERROR, "Kết nối bị đóng giữa chừng"

        if isinstance(exc, socket.timeout):
            return FILE_STATUS_ERROR, "Server không phản hồi (quá thời gian chờ)"

        if isinstance(exc, ConnectionRefusedError):
            return FILE_STATUS_ERROR, "Server từ chối kết nối"

        if isinstance(exc, OSError):
            errno = getattr(exc, "winerror", None) or getattr(exc, "errno", None)
            if errno in {10054, 104, 32, 107, 109}:
                return FILE_STATUS_ERROR, "Kết nối mạng bị đóng bởi phía xa"

        return FILE_STATUS_ERROR, str(exc)

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

                request = {
                    "type": "UPLOAD_REQUEST",
                    "filename": self.file_path.name,
                    "size": total,
                }
                if self.session_id:
                    request["session_id"] = self.session_id
                send_json(sock, request)
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
            status, message = self._classify_exception(exc, self._stop_event.is_set())
            if status == FILE_STATUS_ERROR and self._is_retryable_network_error(exc):
                self._retried = True
                self._emit(FILE_STATUS_ERROR, progress, "0 B/s", "Kết nối đóng giữa chừng, sẽ thử lại sau")
                self.queue_controller.retry_failed(self.key)
                return
            self._emit(status, progress, "0 B/s", message)
        finally:
            # Luôn giải phóng slot để tệp kế tiếp trong hàng đợi được gửi, dù tệp này lỗi hay bị hủy
            if not self._retried:
                self.queue_controller.mark_done(self.key)

    @staticmethod
    def _is_retryable_network_error(exc):
        if isinstance(exc, (ConnectionResetError, BrokenPipeError, EOFError, ConnectionAbortedError, OSError)):
            errno = getattr(exc, "winerror", None) or getattr(exc, "errno", None)
            if errno in {10054, 104, 32, 107, 109}:
                return True
            if isinstance(exc, (ConnectionResetError, BrokenPipeError, EOFError, ConnectionAbortedError)):
                return True
        return False