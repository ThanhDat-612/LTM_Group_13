import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, ttk


class SettingsPanel(ttk.Frame):
    def __init__(self, master=None, title="Cài đặt", **kwargs):
        super().__init__(master, style="Plain.TFrame", **kwargs)
        self.host_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="5000")
        self.upload_dir_var = tk.StringVar(value="server/storage/uploads")

        ttk.Label(self, text="Host", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        self.host_box = ttk.Combobox(self, textvariable=self.host_var, width=16,
                                     values=("127.0.0.1", "0.0.0.0"))
        self.host_box.grid(row=0, column=1, columnspan=2, padx=(10, 0), pady=4, sticky="ew")

        ttk.Label(self, text="Port", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        self.port_entry = ttk.Entry(self, textvariable=self.port_var, width=8)
        self.port_entry.grid(row=1, column=1, columnspan=2, padx=(10, 0), pady=4, sticky="w")

        ttk.Label(self, text="Thư mục lưu", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        self.dir_entry = ttk.Entry(self, textvariable=self.upload_dir_var, width=22)
        self.dir_entry.grid(row=2, column=1, padx=(10, 6), pady=4, sticky="ew")
        self.browse_button = ttk.Button(self, text="Chọn…", style="Small.TButton", command=self.browse)
        self.browse_button.grid(row=2, column=2, pady=4)

        ttk.Label(self, text="Dùng 0.0.0.0 để các máy khác trong mạng LAN kết nối được.",
                  style="Muted.TLabel", wraplength=280, justify="left"
                  ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 6))
        ttk.Button(self, text="Mở thư mục lưu", style="Small.TButton",
                   command=self.open_folder).grid(row=4, column=0, columnspan=3, sticky="w")

        self.columnconfigure(1, weight=1)

    def browse(self):
        path = filedialog.askdirectory(title="Chọn thư mục lưu tệp")
        if path:
            self.upload_dir_var.set(path)

    def open_folder(self):
        path = os.path.abspath(self.upload_dir_var.get().strip() or ".")
        try:
            os.makedirs(path, exist_ok=True)
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except OSError:
            pass

    def set_values(self, host=None, port=None, upload_dir=None):
        if host:
            self.host_var.set(str(host))
        if port:
            self.port_var.set(str(port))
        if upload_dir:
            self.upload_dir_var.set(str(upload_dir))

    def set_enabled(self, enabled):
        """Khoá các ô cấu hình khi server đang chạy."""
        state = ["!disabled"] if enabled else ["disabled"]
        for widget in (self.host_box, self.port_entry, self.dir_entry, self.browse_button):
            widget.state(state)