import os
import socket
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from server.gui import styles
from server.gui.clients_view import ClientsView
from server.gui.log_view import LogView
from server.gui.settings_panel import SettingsPanel
from server.gui.uploads_view import UploadsView

REFRESH_MS = 500


def lan_ip():
    """Địa chỉ IP của máy trong mạng LAN, để cho client biết cần nhập gì."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class ServerWindow(ttk.Frame):
    def __init__(self, master, server):
        super().__init__(master)
        self.server = server
        self.server.set_gui(self)
        self._dirty = False
        self._lan_ip = lan_ip()

        self.master.title("Server Upload Manager")
        self.master.geometry("1120x740")
        self.master.minsize(960, 640)
        styles.apply_styles(self.master)
        try:
            self.master.protocol("WM_DELETE_WINDOW", self._on_close)
        except tk.TclError:
            pass

        wrap = ttk.Frame(self, padding=24)
        wrap.pack(fill="both", expand=True)

        # ---- Tiêu đề + nút điều khiển ----
        head = ttk.Frame(wrap)
        head.pack(fill="x")
        titles = ttk.Frame(head)
        titles.pack(side="left")
        ttk.Label(titles, text="Server Upload Manager", style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text="Nhận tệp từ các client và theo dõi tiến độ theo thời gian thực",
                  style="Subtitle.TLabel").pack(anchor="w")

        self.stop_button = ttk.Button(head, text="Tắt server", style="Danger.TButton", command=self.stop_server)
        self.stop_button.pack(side="right")
        self.start_button = ttk.Button(head, text="Bật server", style="Primary.TButton", command=self.start_server)
        self.start_button.pack(side="right", padx=(0, 8))

        # ---- Thẻ thống kê ----
        self.status_var = tk.StringVar(value="Đang tắt")
        self.connected_var = tk.StringVar(value="0")
        self.uploads_var = tk.StringVar(value="0")
        self.address_var = tk.StringVar(value="-")
        self.host_var = self.address_var   # giữ tên cũ để code bên ngoài không lỗi
        self.port_var = tk.StringVar()

        stats = ttk.Frame(wrap)
        stats.pack(fill="x", pady=16)
        for i in range(4):
            stats.columnconfigure(i, weight=1, uniform="stat")
        self.status_value = self._stat_card(stats, 0, "Trạng thái", self.status_var)
        self._stat_card(stats, 1, "Client đang kết nối", self.connected_var)
        self._stat_card(stats, 2, "Upload đang chạy", self.uploads_var)
        self._stat_card(stats, 3, "Địa chỉ cho client nhập", self.address_var)

        # ---- Thân: trái (cấu hình + client) | phải (upload + log) ----
        body = ttk.Frame(wrap)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")

        self.settings = SettingsPanel(self._card(left, "Cấu hình"))
        self.settings.pack(fill="x")
        self.settings.set_values(server.host, server.port, getattr(server, "upload_dir", None))

        self.clients_title = tk.StringVar(value="Client")
        client_body = self._card(left, self.clients_title, expand=True, pady=(14, 0))
        self.clients = ClientsView(client_body)
        self.clients.pack(fill="both", expand=True)

        self.uploads_title = tk.StringVar(value="Upload đang hoạt động")
        up_body, up_actions = self._card(right, self.uploads_title, expand=True, actions=True)
        self.uploads = UploadsView(up_body)
        self.uploads.pack(fill="both", expand=True)
        ttk.Button(up_actions, text="Xoá mục đã xong", style="Small.TButton",
                   command=self.clear_finished).pack(side="right")

        log_body, log_actions = self._card(right, "Nhật ký", expand=True, pady=(14, 0), actions=True)
        self.logs = LogView(log_body)
        self.logs.pack(fill="both", expand=True)
        ttk.Button(log_actions, text="Lưu log", style="Small.TButton", command=self.logs.save).pack(side="right")
        ttk.Button(log_actions, text="Xoá log", style="Small.TButton", command=self.clear_logs).pack(side="right", padx=(0, 6))

        self._tick()

    # ---------- Dựng giao diện ----------
    def _card(self, parent, title, expand=False, pady=0, actions=False):
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.pack(fill="both" if expand else "x", expand=expand, pady=pady)
        top = ttk.Frame(card, style="Plain.TFrame")
        top.pack(fill="x", pady=(0, 10))
        if isinstance(title, tk.StringVar):
            ttk.Label(top, textvariable=title, style="CardTitle.TLabel").pack(side="left")
        else:
            ttk.Label(top, text=title, style="CardTitle.TLabel").pack(side="left")
        body = ttk.Frame(card, style="Plain.TFrame")
        body.pack(fill="both", expand=True)
        if actions:
            actions_frame = ttk.Frame(top, style="Plain.TFrame")
            actions_frame.pack(side="right")
            return body, actions_frame
        return body

    def _stat_card(self, parent, column, title, var):
        card = ttk.Frame(parent, style="Card.TFrame", padding=(16, 12))
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 12, 0))
        ttk.Label(card, text=title, style="Muted.TLabel").pack(anchor="w")
        value = ttk.Label(card, textvariable=var, style="StatValue.TLabel")
        value.pack(anchor="w", pady=(4, 0))
        return value

    # ---------- Điều khiển server ----------
    def start_server(self):
        if self.server.is_running:
            return
        host = self.settings.host_var.get().strip()
        port_text = self.settings.port_var.get().strip()
        upload_dir = self.settings.upload_dir_var.get().strip()
        if not host:
            messagebox.showerror("Lỗi", "Host không được để trống.")
            return
        try:
            port = int(port_text)
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi", "Port phải là số nguyên từ 1 đến 65535.")
            return
        try:
            if upload_dir:
                os.makedirs(upload_dir, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Lỗi", f"Không tạo được thư mục lưu:\n{exc}")
            return

        # Áp dụng cấu hình người dùng đã nhập vào server
        self.server.host = host
        self.server.port = port
        if upload_dir and hasattr(self.server, "upload_dir"):
            current = self.server.upload_dir
            self.server.upload_dir = Path(upload_dir) if isinstance(current, Path) else upload_dir

        try:
            ok = self.server.start()
        except Exception as exc:
            messagebox.showerror("Không bật được server", str(exc))
            ok = None
        if ok is False:   # ví dụ cổng đang bị chương trình khác dùng
            reason = self.server.logs[-1] if self.server.logs else "Không rõ nguyên nhân"
            messagebox.showerror("Không bật được server", reason)
        self._do_refresh()

    def stop_server(self):
        if not self.server.is_running:
            return
        password = simpledialog.askstring("Xác nhận", "Nhập mật khẩu để tắt server:", show="*", parent=self.master)
        if password is None:
            return
        if password != self.server.stop_password:
            messagebox.showerror("Lỗi", "Mật khẩu không đúng.")
            return
        self.server.stop()
        self._do_refresh()

    def clear_finished(self):
        self.server.clear_finished_uploads()
        self._do_refresh()

    def clear_logs(self):
        try:
            self.server.logs.clear()
        except Exception:
            pass
        self.logs.clear()

    def _on_close(self):
        if self.server.is_running:
            if not messagebox.askokcancel("Thoát", "Server đang chạy. Thoát sẽ tắt server và ngắt mọi upload. Tiếp tục?"):
                return
            try:
                self.server.stop()
            except Exception:
                pass
        self.master.destroy()

    # ---------- Làm mới giao diện ----------
    def refresh(self):
        """Server có thể gọi hàm này từ thread bất kỳ; việc vẽ lại luôn diễn ra ở luồng giao diện."""
        if threading.current_thread() is not threading.main_thread():
            self._dirty = True
            return
        self._do_refresh()

    def _tick(self):
        try:
            self._do_refresh()
        finally:
            self._dirty = False
            self.after(REFRESH_MS, self._tick)

    def _do_refresh(self):
        running = self.server.is_running
        clients = self.server.get_connected_clients()
        uploads = self.server.get_active_uploads()

        self.status_var.set("Đang chạy" if running else "Đang tắt")
        self.status_value.configure(foreground=styles.SUCCESS if running else styles.MUTED)
        self.connected_var.set(str(self.server.get_client_count()))
        running_uploads = [u for u in uploads if styles.status_group(u.get("status", "")) in ("active", "wait")]
        self.uploads_var.set(str(len(running_uploads)))
        self.port_var.set(str(self.server.port))

        host = self.server.host
        shown = self._lan_ip if host in ("0.0.0.0", "") else host
        self.address_var.set(f"{shown}:{self.server.port}")

        self.start_button.state(["disabled" if running else "!disabled"])
        self.stop_button.state(["!disabled" if running else "disabled"])
        self.settings.set_enabled(not running)

        self.clients_title.set(f"Client ({len(clients)})")
        self.uploads_title.set(f"Upload ({len(running_uploads)} đang chạy / {len(uploads)} tổng)")
        self.clients.refresh(clients)
        self.uploads.refresh(uploads)
        self.logs.set_logs(self.server.logs, getattr(self.server, "log_total", None))