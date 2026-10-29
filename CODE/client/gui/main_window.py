import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk

from client.gui import styles
from client.gui.drop_area import DropArea
from client.gui.file_list_view import FileListView
from client.network.session import ClientSession
from client.network.upload_manager import UploadManager

try:
    from tkinterdnd2 import DND_FILES
except Exception:  # pragma: no cover
    DND_FILES = None


class FileTransferApp:
    def __init__(self, root):
        self.root = root
        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="5000")
        self.status = tk.StringVar(value="Chưa kết nối")
        self.ping = tk.StringVar(value="Ping: -- ms")
        self.upload_files = []      # các tệp đang chờ hoặc đang gửi (khoá giống với UploadManager)
        self.manager = None
        self.session = None
        self.connected = False

        root.title("Client Upload Manager")
        root.geometry("820x700")
        root.minsize(720, 580)
        styles.apply_styles(root)

        main = ttk.Frame(root, padding=24)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Upload Manager", style="Title.TLabel").pack(anchor="w")
        ttk.Label(main, text="Gửi tệp từ máy của bạn đến server", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 14))

        # --- Thẻ kết nối ---
        conn = ttk.Frame(main, style="Card.TFrame", padding=16)
        conn.pack(fill="x")
        conn.columnconfigure(1, weight=1)

        ttk.Label(conn, text="IP", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        self.host_entry = ttk.Entry(conn, textvariable=self.host, width=18)
        self.host_entry.grid(row=0, column=1, padx=(8, 16), sticky="ew")
        ttk.Label(conn, text="Port", style="Card.TLabel").grid(row=0, column=2, sticky="w")
        self.port_entry = ttk.Entry(conn, textvariable=self.port, width=8)
        self.port_entry.grid(row=0, column=3, padx=(8, 16))

        self.connect_button = ttk.Button(conn, text="Kết nối", style="Primary.TButton", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=4, padx=(0, 8))
        self.select_button = ttk.Button(conn, text="Chọn file", style="Secondary.TButton", command=self.choose_files)
        self.select_button.grid(row=0, column=5)

        info = ttk.Frame(conn, style="Plain.TFrame")
        info.grid(row=1, column=0, columnspan=6, sticky="w", pady=(14, 0))
        self.ping_label = ttk.Label(info, textvariable=self.ping, style="Ping.TLabel")
        self.ping_label.pack(side="left")
        self.status_label = ttk.Label(info, textvariable=self.status, style="Muted.TLabel")
        self.status_label.pack(side="left", padx=(12, 0))

        self.host_entry.bind("<Return>", lambda e: self.toggle_connection() if not self.connected else None)
        self.port_entry.bind("<Return>", lambda e: self.toggle_connection() if not self.connected else None)

        # --- Vùng kéo thả ---
        self.drop_area = DropArea(main, callback=self.choose_files)
        self.drop_area.pack(fill="x", pady=16)

        # --- Danh sách ---
        head = ttk.Frame(main)
        head.pack(fill="x", pady=(0, 8))
        ttk.Label(head, text="Danh sách tải lên", style="Section.TLabel").pack(side="left")
        ttk.Button(head, text="Xoá danh sách", style="Secondary.TButton",
                   command=self.clear_list).pack(side="right")
        ttk.Button(head, text="Hủy tất cả", style="Cancel.TButton",
                   command=self.cancel_all).pack(side="right", padx=(0, 8))

        self.file_list = FileListView(main, on_cancel=self.cancel_file)
        self.file_list.pack(fill="both", expand=True)

        self.root.bind("<Control-o>", lambda event: self.choose_files())
        self.root.bind("<Control-v>", self._paste)
        if DND_FILES is not None:
            try:
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind('<<Drop>>', self._drop_root)
            except Exception:
                pass

    # ---------- Kết nối / ngắt kết nối ----------
    def _set_status(self, text, color=styles.MUTED):
        self.status.set(text)
        self.status_label.configure(foreground=color)

    def toggle_connection(self):
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        host = self.host.get().strip()
        port_text = self.port.get().strip()
        if not host:
            self._set_status("IP không được để trống", styles.DANGER)
            return
        try:
            port = int(port_text)
        except ValueError:
            self._set_status("Port phải là số nguyên", styles.DANGER)
            return

        # Kiểm tra mạng ở thread riêng để cửa sổ không bị đơ
        self.connect_button.state(["disabled"])
        self._set_status(f"Đang kết nối đến {host}:{port}…", styles.MUTED)
        threading.Thread(target=self._probe, args=(host, port), daemon=True).start()

    def _probe(self, host, port):
        session = ClientSession(host, port,
                                on_lost=lambda: self.root.after(0, self._lost),
                                on_ping=lambda ms: self.root.after(0, self._on_ping, ms))
        try:
            ping_ms = session.connect(timeout=3)
            ok = True
        except (OSError, EOFError, ValueError):
            ping_ms, ok = None, False
        self.root.after(0, self._probe_done, host, port, ok, ping_ms, session)

    def _probe_done(self, host, port, ok, ping_ms, session):
        self.connect_button.state(["!disabled"])
        if ok:
            self.connected = True
            self.session = session
            self.manager = None  # manager mới sẽ dùng IP/Port hiện tại
            self._set_status(f"● Đã kết nối đến {host}:{port}", styles.SUCCESS)
            self.ping.set(f"Ping: {ping_ms} ms")
            self.connect_button.configure(text="Ngắt kết nối", style="Danger.TButton")
            self.host_entry.state(["disabled"])
            self.port_entry.state(["disabled"])
        else:
            self._set_status(f"● Không thể kết nối đến {host}:{port}", styles.DANGER)
            self.ping.set("Ping: -- ms")

    def _on_ping(self, ms):
        if self.connected:
            self.ping.set(f"Ping: {ms} ms")

    def _lost(self):
        """Phiên kết nối bị server đóng (ví dụ server tắt)."""
        if self.connected:
            self.disconnect()
            self._set_status("● Mất kết nối đến server", styles.DANGER)

    def disconnect(self):
        """Ngắt kết nối: hủy mọi upload đang chạy / đang chờ và đưa giao diện về trạng thái ban đầu."""
        if self.session:
            self.session.close()
            self.session = None
        if self.manager:
            self.manager.stop()
            self.manager = None
        self.connected = False
        self.connect_button.configure(text="Kết nối", style="Primary.TButton")
        self.host_entry.state(["!disabled"])
        self.port_entry.state(["!disabled"])
        self.ping.set("Ping: -- ms")
        self._set_status("Đã ngắt kết nối", styles.MUTED)

    # ---------- Chọn / thả tệp ----------
    def choose_files(self, paths=None):
        if paths:  # được gọi từ vùng kéo thả
            self.handle_drop(paths)
            return
        files = filedialog.askopenfilenames(title="Chọn file để upload")
        if files:
            self.handle_drop(files)

    def _paste(self, event=None):
        try:
            self.handle_drop(self.root.clipboard_get())
        except tk.TclError:
            pass

    def _drop_root(self, event):
        self.handle_drop(event.data)

    def handle_drop(self, file_list):
        if isinstance(file_list, str):
            try:
                sources = list(self.root.tk.splitlist(file_list))
            except Exception:
                sources = [file_list]
        elif isinstance(file_list, (list, tuple)):
            sources = list(file_list)
        else:
            sources = []

        new_files = []
        for path in sources:
            clean = (path or "").strip().strip("{}")
            if not clean or not os.path.isfile(clean) or clean in self.upload_files:
                continue
            self.upload_files.append(clean)
            new_files.append(clean)
            self.file_list.add_or_update(os.path.basename(clean), "chờ", 0, "0 B/s",
                                         "Đang chờ trong hàng đợi")
        if not new_files:
            return

        if not self.manager:
            host = self.host.get().strip() or "127.0.0.1"
            port = self.port.get().strip() or "5000"
            self.manager = UploadManager(host, port, self._on_upload_update, max_concurrent=3)
        self.manager.add_files(new_files)  # chỉ gửi tệp mới

    # ---------- Hủy ----------
    def cancel_file(self, file_name):
        """Được gọi từ nút Hủy trên từng thẻ tệp."""
        if not self.manager:
            return
        for path in list(self.upload_files):
            if os.path.basename(path) == file_name:
                self.manager.cancel(path)

    def cancel_all(self):
        if self.manager:
            self.manager.cancel_all()

    def clear_list(self):
        """Xoá danh sách trên giao diện (các upload đang chạy sẽ bị hủy trước)."""
        self.cancel_all()
        self.file_list.clear()
        self.upload_files.clear()

    # ---------- Cập nhật từ UploadManager ----------
    def _on_upload_update(self, file_name, status, progress, speed, detail):
        # UploadManager chạy ở thread khác -> chuyển về luồng giao diện
        self.root.after(0, self._apply_update, file_name, status, progress, speed, detail)

    def _apply_update(self, file_name, status, progress, speed, detail):
        if file_name not in self.file_list.items:   # danh sách vừa bị xoá, bỏ qua cập nhật muộn
            return
        self.file_list.add_or_update(file_name, status, progress, speed, detail)
        color, _, _ = styles.status_kind(status)
        self._set_status(f"{file_name} — {status}", color)
        if styles.is_finished(status):
            # Giải phóng khỏi danh sách theo dõi để có thể gửi lại tệp này sau (ví dụ sau khi lỗi / hủy)
            self.upload_files = [p for p in self.upload_files if os.path.basename(p) != file_name]

    def run(self):
        self.root.mainloop()