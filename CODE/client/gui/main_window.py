from common.protocol import recv_json, send_json
import tkinter as tk
from tkinter import ttk

from client.network.connection import create_connection, close_connection


class FileTransferApp:
    def __init__(self, root):
        self.root = root
        self.sock = None

        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="5000")
        self.status = tk.StringVar(value="Chưa kết nối")

        root.title("Client")
        root.geometry("650x170")
        root.minsize(580, 170)

        frame = ttk.Frame(root, padding=20)
        frame.grid(sticky="w")

        ttk.Label(frame, text="IP:").grid(
            row=0, column=0, padx=(0, 8)
        )
        self.host_entry = ttk.Entry(frame, textvariable=self.host)
        self.host_entry.grid(row=0, column=1, padx=(0, 12))

        ttk.Label(frame, text="Port:").grid(
            row=0, column=2, padx=(0, 8)
        )
        self.port_entry = ttk.Entry(
            frame, textvariable=self.port, width=7
        )
        self.port_entry.grid(row=0, column=3, padx=(0, 12))

        self.connect_button = ttk.Button(
            frame, text="Connect", command=self.connect
        )
        self.connect_button.grid(row=0, column=4, padx=(0, 8))

        self.disconnect_button = ttk.Button(
            frame,
            text="Disconnect",
            command=self.disconnect,
            state="disabled",
        )
        self.disconnect_button.grid(row=0, column=5)

        ttk.Label(frame, textvariable=self.status).grid(
            row=1, column=0, columnspan=6,
            sticky="w", pady=(16, 0)
        )

        self.host_entry.focus_set()
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def connect(self):
        if self.sock is not None:
            self.status.set("Bạn đã kết nối rồi")
            return

        host = self.host.get().strip()

        try:
            port = int(self.port.get().strip())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            self.status.set("Port phải từ 1 đến 65535")
            return

        if not host:
            self.status.set("IP không được để trống")
            return

        sock = None

        try:
            # Bước 1: Mở kết nối TCP
            sock = create_connection(host, port, timeout=3)

            # Bước 2: Gửi HELLO để server đăng ký phiên client
            send_json(sock, {"type": "HELLO"})

            # Bước 3: Chờ server xác nhận
            response = recv_json(sock)

            if not response or response.get("type") != "WELCOME":
                raise ConnectionError("Server không xác nhận kết nối")

            # Bước 4: Giữ kết nối để client hiển thị trong danh sách
            sock.settimeout(None)
            self.sock = sock

            self.status.set(f"Đã kết nối đến {host}:{port}")
            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")

        except (OSError, ValueError, TypeError) as error:
            if sock is not None:
                close_connection(sock)

            self.sock = None
            self.status.set(f"Kết nối thất bại: {error}")
    def disconnect(self):
        if self.sock is not None:
            close_connection(self.sock)
            self.sock = None

        self.status.set("Đã ngắt kết nối")
        self.connect_button.config(state="normal")
        self.disconnect_button.config(state="disabled")

    def on_close(self):
        self.disconnect()
        self.root.destroy()
