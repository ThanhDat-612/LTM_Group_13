import socket
import threading
import time
from datetime import datetime
from pathlib import Path

from common.utils import ensure_dir, timestamp_label
from server.config_loader import load_config
from server.duplicate_policy import resolve_duplicate_name
from server.logger import SessionLogger
from server.upload_handler import UploadHandler

MAX_LOGS = 200
MAX_UPLOAD_HISTORY = 500    # số dòng tối đa trong bảng upload; vượt quá thì bỏ dòng đã kết thúc cũ nhất


class Server:
    def __init__(self, config_path="config.json"):
        config = load_config(config_path)   # ném ConfigError nếu config.json sai
        self.config = config
        self._config_path = config.path
        self.host = config.host
        self.port = config.port
        self.upload_dir = str(config.upload_dir)
        self.stop_password = config.stop_password
        self.max_file_size = config.max_file_size_mb * 1024 * 1024   # 0 = không giới hạn

        self.server_socket = None
        self.is_running = False
        self.accept_thread = None
        self.lock = threading.RLock()
        self.connections = {}        # mọi socket đang mở -> địa chỉ (để tắt server có thể ngắt hết)
        self.connected_clients = {}  # chỉ các phiên HELLO: những client đang thật sự "kết nối"
        self.active_uploads = {}
        self.logs = []
        self.log_total = 0           # tổng số dòng log đã ghi (giao diện dùng để biết dòng nào mới)
        self._active_handlers = 0    # số luồng xử lý kết nối còn chạy (để tắt server chờ chúng xong)
        self.gui = None
        self.file_logger = SessionLogger(config.log_dir, config.max_log_files)
        ensure_dir(self.upload_dir)

    def set_gui(self, gui):
        self.gui = gui

    # ---------- Log ----------
    def log(self, message):
        entry = f"[{timestamp_label()}] {message}"
        with self.lock:
            self.logs.append(entry)
            self.log_total += 1
            if len(self.logs) > MAX_LOGS:
                del self.logs[:-MAX_LOGS]   # cắt tại chỗ, không tạo list mới
        self.file_logger.write(entry)      # ghi ra tệp log của phiên hiện tại (nếu server đang bật)
        if self.gui is not None:
            try:
                self.gui.refresh()
            except Exception:
                pass

    # ---------- Dữ liệu cho giao diện ----------
    def get_connected_clients(self):
        with self.lock:
            return [dict(c) for c in self.connected_clients.values()]

    def get_client_count(self):
        with self.lock:
            return len(self.connected_clients)

    def get_active_uploads(self):
        """Toàn bộ upload (đang chạy lẫn đã kết thúc), cũ nhất trước."""
        with self.lock:
            return [{k: v for k, v in e.items() if k != "finished_at"} for e in self.active_uploads.values()]

    def clear_finished_uploads(self):
        with self.lock:
            for key in [k for k, e in self.active_uploads.items() if "finished_at" in e]:
                del self.active_uploads[key]

    def _trim_upload_history(self):
        excess = len(self.active_uploads) - MAX_UPLOAD_HISTORY
        if excess <= 0:
            return
        for key in [k for k, e in self.active_uploads.items() if "finished_at" in e][:excess]:
            del self.active_uploads[key]

    def set_client_status(self, client_socket, status):
        with self.lock:
            if client_socket in self.connected_clients:
                self.connected_clients[client_socket]["status"] = status

    def register_session(self, client_socket):
        """Client gửi HELLO: tính là một client đang kết nối (khác với các kết nối ngắn chỉ để gửi tệp)."""
        with self.lock:
            addr = self.connections.get(client_socket)
            if addr is None or client_socket in self.connected_clients:
                return
            self.connected_clients[client_socket] = {"address": addr, "status": "đã kết nối"}
        self.log(f"Client {addr} đã kết nối")

    # ---------- Quản lý upload ----------
    def update_upload(self, client_label, file_name, status, progress, speed):
        key = f"{client_label}:{file_name}"
        with self.lock:
            entry = self.active_uploads.setdefault(key, {})
            self._trim_upload_history()
            entry.update(file=file_name, client=str(client_label), status=status,
                         progress=progress, speed=speed)
            entry.pop("finished_at", None)

    def finish_upload(self, client_label, file_name):
        """Đánh dấu đã kết thúc (dòng vẫn được giữ trong bảng, có thể xoá bằng clear_finished_uploads)."""
        key = f"{client_label}:{file_name}"
        with self.lock:
            if key in self.active_uploads:
                self.active_uploads[key]["finished_at"] = time.monotonic()

    def reserve_file(self, safe_name, upload_dir):
        """Chọn tên không trùng và giữ chỗ nguyên tử bằng cách tạo tệp rỗng.
        Nhờ đó hai client cùng gửi một tên tệp không bao giờ ghi chung một tệp."""
        upload_dir = Path(upload_dir)
        with self.lock:
            for _ in range(1000):
                candidate = upload_dir / resolve_duplicate_name(safe_name, upload_dir)
                try:
                    with open(candidate, "xb"):
                        pass
                    return candidate
                except FileExistsError:
                    continue
        raise OSError("Không tìm được tên tệp khả dụng")

    # ---------- Bật / tắt ----------
    def start(self):
        with self.lock:
            if self.is_running:
                return True
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((self.host, self.port))
                sock.listen(20)
                sock.settimeout(1.0)   # để vòng accept kiểm tra cờ dừng định kỳ
            except OSError as exc:
                self.log(f"Không thể khởi động server: {exc}")
                return False
            self.server_socket = sock
            self.is_running = True

        # Mỗi lần bật server là một tệp log mới, ghi tới khi tắt server
        try:
            self.file_logger.start(header=f"=== Phiên server bắt đầu lúc {datetime.now():%Y-%m-%d %H:%M:%S} ===")
            log_note = f"Tệp log phiên này: {self.file_logger.path}"
        except OSError as exc:
            log_note = f"Không tạo được tệp log ({exc}), nhật ký chỉ hiển thị trên giao diện"

        ensure_dir(self.upload_dir)
        for stale in Path(self.upload_dir).glob(".*.part"):   # dọn tệp tạm còn sót lại sau lần chạy trước
            try:
                stale.unlink()
            except OSError:
                pass
        self.accept_thread = threading.Thread(target=self._accept_loop, args=(sock,), daemon=True)
        self.accept_thread.start()
        self.log(f"Server đã bắt đầu lắng nghe trên {self.host}:{self.port}")
        self.log(f"Thư mục lưu tệp: {self.upload_dir}")
        limit = f"{self.config.max_file_size_mb} MB" if self.max_file_size else "không giới hạn"
        self.log(f"Dung lượng tối đa mỗi tệp: {limit}")
        for warning in self.config.warnings:
            self.log(f"Cảnh báo cấu hình: {warning}")
        self.log(log_note)
        return True

    def _accept_loop(self, sock):
        while self.is_running and sock is self.server_socket:
            try:
                client_socket, client_address = sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            addr = f"{client_address[0]}:{client_address[1]}"
            with self.lock:
                self.connections[client_socket] = addr
                self._active_handlers += 1
            threading.Thread(target=self.handle_client, args=(client_socket, client_address),
                             daemon=True).start()

    def handle_client(self, client_socket, client_address):
        addr = f"{client_address[0]}:{client_address[1]}"
        try:
            UploadHandler(client_socket, client_address, self).process()
        except Exception as exc:
            self.log(f"Lỗi xử lý kết nối {addr}: {exc}")
        finally:
            with self.lock:
                self.connections.pop(client_socket, None)
                was_session = self.connected_clients.pop(client_socket, None) is not None
            try:
                client_socket.close()
            except OSError:
                pass
            if was_session:   # chỉ ghi log khi một client thật sự rời đi, không ghi cho mỗi lần gửi xong một tệp
                self.log(f"Client {addr} đã ngắt kết nối")
            with self.lock:
                self._active_handlers -= 1

    def stop(self):
        with self.lock:
            if not self.is_running:
                return
            self.is_running = False
            sock, self.server_socket = self.server_socket, None
            clients = list(self.connections.keys())
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        # Ngắt cả các client đang kết nối để các upload dở dang dừng lại và dọn tệp tạm
        for client in clients:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                client.close()
            except OSError:
                pass
        # Chờ các luồng xử lý dọn dẹp xong (tối đa 3 giây) để log của chúng kịp vào tệp
        deadline = time.monotonic() + 3
        while self._active_handlers > 0 and time.monotonic() < deadline:
            time.sleep(0.02)
        self.log("Server đã dừng hoạt động")
        self.file_logger.stop(footer=f"=== Phiên server kết thúc lúc {datetime.now():%Y-%m-%d %H:%M:%S} ===")