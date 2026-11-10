import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from client.network.connection import check_connection
from client.network.upload_worker import upload_file


class FileTransferApp:
    def __init__(self, root):
        self.root = root
        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="5000")
        self.status = tk.StringVar(value="Chưa kết nối")

        root.title("Client")
        root.geometry("620x190")
        root.minsize(560, 190)

        frame = ttk.Frame(root, padding=20)
        frame.grid(sticky="nsew")

        ttk.Label(frame, text="IP:").grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.host_entry = ttk.Entry(frame, textvariable=self.host, width=20)
        self.host_entry.grid(row=0, column=1, padx=(0, 12))

        ttk.Label(frame, text="Port:").grid(row=0, column=2, padx=(0, 8), sticky="w")
        self.port_entry = ttk.Entry(frame, textvariable=self.port, width=8)
        self.port_entry.grid(row=0, column=3, padx=(0, 12))

        self.connect_button = ttk.Button(frame, text="Connect", command=self.connect)
        self.connect_button.grid(row=0, column=4)

        self.upload_button = ttk.Button(frame, text="Upload file", command=self.choose_file)
        self.upload_button.grid(row=1, column=0, columnspan=5, sticky="w", pady=(18, 0))

        self.status_label = ttk.Label(frame, textvariable=self.status, wraplength=560)
        self.status_label.grid(row=2, column=0, columnspan=5, sticky="w", pady=(16, 0))
        self.host_entry.focus_set()

    def _server_address(self):
        host = self.host.get().strip()
        if not host:
            raise ValueError("IP không được để trống")
        try:
            port = int(self.port.get().strip())
        except ValueError as exc:
            raise ValueError("Port phải là số nguyên") from exc
        if not 1 <= port <= 65535:
            raise ValueError("Port phải nằm trong khoảng 1–65535")
        return host, port

    def connect(self):
        try:
            host, port = self._server_address()
            check_connection(host, port, timeout=3)
            self.status.set(f"Đã kết nối đến {host}:{port}")
        except (ValueError, OSError) as exc:
            self.status.set(f"Không thể kết nối: {exc}")

    def choose_file(self):
        file_path = filedialog.askopenfilename(parent=self.root)
        if not file_path:
            return
        try:
            host, port = self._server_address()
        except ValueError as exc:
            messagebox.showerror("Thông tin Server", str(exc), parent=self.root)
            return
        self.upload_button.config(state="disabled")
        self.status.set(f"Đang upload: {file_path}")
        threading.Thread(target=self._upload_in_background,
                         args=(host, port, file_path), daemon=True).start()

    def _upload_in_background(self, host, port, file_path):
        try:
            result = upload_file(host, port, file_path)
            self.root.after(0, self._show_upload_result, result)
        except Exception as exc:
            self.root.after(0, self._show_upload_error, str(exc))

    def _show_upload_result(self, result):
        self.upload_button.config(state="normal")
        if result.get("success"):
            self.status.set(f"Upload thành công: {result.get('filename', '')}")
        else:
            self.status.set(f"Upload bị từ chối: {result.get('code', 'ERROR')} - {result.get('message', '')}")

    def _show_upload_error(self, message):
        self.upload_button.config(state="normal")
        self.status.set(f"Upload thất bại: {message}")
