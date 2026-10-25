import os
import shutil
import socket
import time
from pathlib import Path

from common.protocol import recv_exact, recv_json, send_json
from common.utils import format_speed
from server.validator import validate_filename

MAX_CHUNK = 4 * 1024 * 1024          # khối dữ liệu tối đa chấp nhận (client dùng CHUNK_SIZE nhỏ hơn nhiều)
IDLE_TIMEOUT = 60                    # giây, client im lặng quá lâu sẽ bị ngắt
DISK_MARGIN = 50 * 1024 * 1024       # chừa lại ít nhất 50 MB trống trên ổ đĩa
PROGRESS_INTERVAL = 0.5

ST_RECEIVING = "đang tải"
ST_DONE = "hoàn tất"
ST_ERROR = "lỗi"
ST_DISCONNECTED = "bị ngắt"


class ClientDisconnected(Exception):
    pass


def _fmt_size(num_bytes):
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024


class UploadHandler:
    def __init__(self, client_socket, client_address, server):
        self.client_socket = client_socket
        self.client_address = client_address
        self.server = server
        self.label = f"{client_address[0]}:{client_address[1]}"

    # ---------- Vòng lặp chính ----------
    def process(self):
        self.client_socket.settimeout(IDLE_TIMEOUT)
        while True:
            try:
                message = recv_json(self.client_socket)
            except (OSError, EOFError, ValueError):
                break
            if not message:
                break

            message_type = message.get("type")
            if message_type == "UPLOAD_REQUEST":
                self._handle_upload_request(message)
                continue
            if message_type == "HELLO":
                self.server.register_session(self.client_socket)
                self._safe_send({"type": "WELCOME", "status": "ok"})
                continue
            if message_type == "PING":
                self._safe_send({"type": "PONG", "status": "ok"})
                continue
            break

    # ---------- Tiện ích ----------
    def _safe_send(self, payload):
        try:
            send_json(self.client_socket, payload)
            return True
        except OSError:
            return False

    def _reject(self, message, log_message=None):
        self._safe_send({"type": "UPLOAD_ERROR", "message": message})
        self.server.log(log_message or f"Từ chối upload từ {self.label}: {message}")

    def _recv_header(self):
        try:
            header = recv_json(self.client_socket)
        except socket.timeout:
            raise ValueError("Quá thời gian chờ dữ liệu từ client")
        except (EOFError, OSError):
            raise ClientDisconnected()
        if not header:
            raise ValueError("Khung dữ liệu rỗng")
        return header

    def _recv_chunk(self, size):
        try:
            return recv_exact(self.client_socket, size)
        except socket.timeout:
            raise ValueError("Quá thời gian chờ dữ liệu từ client")
        except (EOFError, OSError):
            raise ClientDisconnected()

    @staticmethod
    def _discard(*paths):
        for path in paths:
            try:
                Path(path).unlink()
            except OSError:
                pass

    # ---------- Nhận một tệp ----------
    def _handle_upload_request(self, message):
        filename = message.get("filename", "")
        try:
            expected_size = int(message.get("size"))
            if expected_size < 0:
                raise ValueError
        except (TypeError, ValueError):
            self._reject("Thiếu hoặc sai dung lượng tệp")
            return

        try:
            safe_name = validate_filename(filename)
        except ValueError as exc:
            self._reject(str(exc), f"Client {self.label} gửi tên file không hợp lệ: {filename!r}")
            return

        max_size = getattr(self.server, "max_file_size", 0)
        if max_size and expected_size > max_size:
            self._reject(f"Tệp vượt quá dung lượng tối đa ({max_size // (1024 * 1024)} MB)")
            return

        upload_dir = Path(self.server.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        try:
            if expected_size + DISK_MARGIN > shutil.disk_usage(upload_dir).free:
                self._reject("Server không đủ dung lượng ổ đĩa")
                return
        except OSError:
            pass

        try:
            final_path = self.server.reserve_file(safe_name, upload_dir)
        except OSError as exc:
            self._reject(f"Server không tạo được tệp: {exc}")
            return
        temp_path = final_path.with_name(f".{final_path.name}.part")

        self.server.update_upload(self.label, safe_name, ST_RECEIVING, 0, "0 B/s")
        self.server.set_client_status(self.client_socket, "đang gửi")
        if not self._safe_send({"type": "UPLOAD_ACK", "status": "accepted", "final_name": final_path.name}):
            self._discard(final_path)
            self.server.update_upload(self.label, safe_name, ST_DISCONNECTED, 0, "0 B/s")
            self.server.finish_upload(self.label, safe_name)
            return
        self.server.log(f"Bắt đầu nhận file {safe_name} ({_fmt_size(expected_size)}) từ {self.label}")

        received = 0
        committed = False
        start_time = last_update = time.monotonic()

        try:
            with open(temp_path, "wb") as temp_file:
                while True:
                    header = self._recv_header()
                    kind = header.get("type")
                    if kind == "UPLOAD_DONE":
                        break
                    if kind != "FILE_DATA":
                        raise ValueError(f"Loại tin nhắn dữ liệu không hợp lệ: {kind}")

                    chunk_size = int(header.get("size", 0) or 0)
                    if chunk_size <= 0:
                        continue
                    if chunk_size > MAX_CHUNK:
                        raise ValueError("Khối dữ liệu quá lớn")
                    if received + chunk_size > expected_size:
                        raise ValueError("Client gửi vượt quá dung lượng đã khai báo")

                    temp_file.write(self._recv_chunk(chunk_size))
                    received += chunk_size

                    now = time.monotonic()
                    if now - last_update >= PROGRESS_INTERVAL:
                        progress = 100 if expected_size == 0 else min(int(received / expected_size * 100), 100)
                        speed = received / max(now - start_time, 0.1)
                        self.server.update_upload(self.label, safe_name, ST_RECEIVING, progress, format_speed(speed))
                        last_update = now

            if received != expected_size:
                raise ValueError(f"Dung lượng nhận được không khớp: mong đợi {expected_size}, thực tế {received}")

            os.replace(temp_path, final_path)   # thay cho tệp giữ chỗ đã tạo lúc đầu
            committed = True
            self.server.update_upload(self.label, safe_name, ST_DONE, 100, "0 B/s")
            elapsed = max(time.monotonic() - start_time, 0.001)
            renamed = f" (đổi tên từ {safe_name})" if final_path.name != safe_name else ""
            self.server.log(f"Đã nhận hoàn tất {final_path.name}{renamed} - {_fmt_size(received)}, "
                            f"{elapsed:.1f}s, {format_speed(received / elapsed)} - từ {self.label}")
            self._safe_send({"type": "UPLOAD_RESULT", "status": "success", "final_name": final_path.name})

        except ClientDisconnected:
            self._discard(temp_path, final_path)
            self.server.update_upload(self.label, safe_name, ST_DISCONNECTED, 0, "0 B/s")
            self.server.log(f"Client {self.label} ngắt kết nối khi đang gửi {safe_name} "
                            f"(đã nhận {_fmt_size(received)}/{_fmt_size(expected_size)}), đã xoá tệp dở")
        except Exception as exc:
            if not committed:
                self._discard(temp_path, final_path)
            self.server.update_upload(self.label, safe_name, ST_ERROR, 0, "0 B/s")
            self.server.log(f"Lỗi khi nhận {safe_name} từ {self.label} (đã nhận {_fmt_size(received)}): {exc}")
            self._safe_send({"type": "UPLOAD_RESULT", "status": "error", "message": str(exc)})
        finally:
            self.server.finish_upload(self.label, safe_name)
            self.server.set_client_status(self.client_socket, "connected")