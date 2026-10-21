import socket
import threading
import json
import os
from pathlib import Path
from server.upload_handler import UploadHandler

class Server:
    def __init__(self, config_path="config.json"):
        self._config_path = self._resolve_config_path(config_path)
        self.load_config(self._config_path)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Cho phép tái sử dụng cổng ngay sau khi tắt server
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_running = False

    def _resolve_config_path(self, config_path):
        path = Path(config_path)
        if path.is_absolute():
            return path

        candidates = [
            Path(__file__).resolve().parent.parent / path,
            Path.cwd() / path,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def load_config(self, config_path):
        """Đọc file cấu hình chung host và port theo cấu trúc project"""
        defaults = {
            "host": "127.0.0.1",
            "port": 5000,
        }

        config_path = Path(config_path)
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}

        self.host = config.get("server_host", config.get("host", defaults["host"]))
        self.port = config.get("server_port", config.get("port", defaults["port"]))

    def start(self):
        """Khởi chạy server, bind cổng và lắng nghe kết nối liên tục[cite: 1]"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5) # Hàng đợi kết nối chờ
            self.is_running = True
            print(f"[SERVER STARTED] Đang lắng nghe tại {self.host}:{self.port}...")

            while self.is_running:
                try:
                    # Chấp nhận kết nối từ client[cite: 1]
                    client_socket, client_address = self.server_socket.accept()
                    print(f"[NEW CONNECTION] Kết nối mới từ địa chỉ: {client_address}")
                    
                    # Quản lý luồng xử lý riêng biệt cho từng client kết nối đến[cite: 1]
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if not self.is_running:
                        break
                    print(f"[ERROR] Lỗi khi chấp nhận kết nối: {e}")
        except Exception as e:
            print(f"[FATAL ERROR] Không thể khởi động server: {e}")
        finally:
            self.stop()

    def handle_client(self, client_socket, client_address):
        """Luồng riêng biệt phục vụ riêng cho 1 client[cite: 1]"""
        try:
            # Giao tiếp và xử lý nhận file, .part, trùng tên thông qua UploadHandler
            handler = UploadHandler(client_socket, client_address)
            handler.process()
        except Exception as e:
            print(f"[CLIENT ERROR] Lỗi xử lý client {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"[DISCONNECT] Đã đóng kết nối với {client_address}")

    def stop(self):
        """Dừng server và đóng socket"""
        self.is_running = False
        try:
            self.server_socket.close()
            print("[SERVER STOPPED] Server đã dừng hoạt động thành công.")
        except Exception as e:
            print(f"[ERROR] Lỗi khi đóng socket server: {e}")

