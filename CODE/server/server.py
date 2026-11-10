import json
import socket
import threading
from pathlib import Path

from server.upload_handler import UploadHandler


class Server:
    def __init__(self, config_path="config.json"):
        self._config_path = self._resolve_config_path(config_path)
        self.load_config(self._config_path)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.settimeout(1.0)
        self.is_running = False
        self._upload_slots = threading.BoundedSemaphore(self.max_concurrent_uploads)

    def _resolve_config_path(self, config_path):
        path = Path(config_path)
        if path.is_absolute():
            return path
        candidates = [Path(__file__).resolve().parent.parent / path, Path.cwd() / path]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def load_config(self, config_path):
        defaults = {"host": "127.0.0.1", "port": 5000, "max_concurrent_uploads": 3,
                    "chunk_size": 65536, "timeout_seconds": 30, "upload_dir": "uploads",
                    "max_file_size_mb": 500}
        config_path = Path(config_path)
        config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
        self.host = config.get("server_host", config.get("host", defaults["host"]))
        self.port = int(config.get("server_port", config.get("port", defaults["port"])))
        self.max_concurrent_uploads = max(1, int(config.get("max_concurrent_uploads", defaults["max_concurrent_uploads"])))
        self.chunk_size = int(config.get("chunk_size", defaults["chunk_size"]))
        self.timeout_seconds = int(config.get("timeout_seconds", defaults["timeout_seconds"]))
        upload_dir = Path(config.get("upload_dir", defaults["upload_dir"]))
        self.upload_dir = upload_dir if upload_dir.is_absolute() else Path(__file__).resolve().parent.parent / upload_dir
        self.max_file_size_mb = int(config.get("max_file_size_mb", defaults["max_file_size_mb"]))

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_concurrent_uploads * 2)
            self.is_running = True
            print(f"[SERVER STARTED] {self.host}:{self.port}")
            print(f"[SECURITY ACTIVE] max_size={self.max_file_size_mb}MB, upload_dir={self.upload_dir}")
            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    if not self._upload_slots.acquire(blocking=False):
                        try:
                            client_socket.sendall(b'{"type":"ERROR","code":"SERVER_BUSY","message":"Upload limit reached."}\n')
                        finally:
                            client_socket.close()
                        print(f"[SECURITY BLOCK] {client_address}: concurrent upload limit reached")
                        continue
                    thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address), daemon=True)
                    thread.start()
                except socket.timeout:
                    continue
                except OSError:
                    if self.is_running:
                        print("[SERVER ERROR] Socket accept failed")
                    break
        except Exception as exc:
            print(f"[FATAL ERROR] Cannot start server: {exc}")
        finally:
            self.stop()

    def handle_client(self, client_socket, client_address):
        try:
            handler = UploadHandler(client_socket, client_address, self.upload_dir,
                                    self.max_file_size_mb, self.chunk_size, self.timeout_seconds)
            handler.process()
        finally:
            client_socket.close()
            self._upload_slots.release()
            print(f"[DISCONNECT] {client_address}")

    def stop(self):
        self.is_running = False
        try:
            self.server_socket.close()
        except OSError:
            pass
        print("[SERVER STOPPED]")
