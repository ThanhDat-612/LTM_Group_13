import tkinter as tk
from tkinter import ttk


class FileTransferApp:
    
    def __init__(self, root):
        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="5000")
        self.status = tk.StringVar(value="Chưa kết nối")

        root.title("Client")
        root.geometry("560x150")
        root.minsize(500, 150)

        frame = ttk.Frame(root, padding=20)
        frame.grid()

        ttk.Label(frame, text="IP:").grid(row=0, column=0, padx=(0, 8))
        self.host_entry = ttk.Entry(frame, textvariable=self.host)
        self.host_entry.grid(row=0, column=1, padx=(0, 12))

        ttk.Label(frame, text="Port:").grid(row=0, column=2, padx=(0, 8))
        self.port_entry = ttk.Entry(frame, textvariable=self.port, width=7)
        self.port_entry.grid(row=0, column=3, padx=(0, 12))

        self.connect_button = ttk.Button(frame, text="Connect", command=self.connect)
        self.connect_button.grid(row=0, column=4)

        self.status_label = ttk.Label(frame, textvariable=self.status)
        self.status_label.grid(row=1, column=0, columnspan=5, sticky="w", pady=(16, 0))
        self.host_entry.focus_set()

    def connect(self):
        # Sẽ bổ sung xử lý kết nối sau.
        pass
