import tkinter as tk
from tkinter import ttk

from client.gui import styles


class ProgressItem(ttk.Frame):
    def __init__(self, master, file_name, status="chờ", progress=0, speed="0 B/s", detail="", on_cancel=None):
        super().__init__(master, style="Card.TFrame", padding=(14, 10))
        self.file_name = file_name
        self.on_cancel = on_cancel
        self.status_var = tk.StringVar()
        self.progress_var = tk.DoubleVar(value=progress)
        self.speed_var = tk.StringVar(value=speed)
        self.detail_var = tk.StringVar(value=detail)
        self.percent_var = tk.StringVar()

        self.icon = tk.Label(self, width=2, font=(styles.FONT, 12, "bold"),
                             bg=styles.CARD)
        self.icon.grid(row=0, column=0, rowspan=3, sticky="n", padx=(0, 12))

        ttk.Label(self, text=file_name, style="Card.TLabel", font=styles.F_BOLD,
                  anchor="w").grid(row=0, column=1, sticky="w")
        self.status_label = tk.Label(self, textvariable=self.status_var,
                                     font=styles.F_SMALL, bg=styles.CARD)
        self.status_label.grid(row=0, column=2, sticky="e", padx=(10, 0))
        self.cancel_button = ttk.Button(self, text="Hủy", style="Cancel.TButton",
                                        command=self._cancel, takefocus=False)
        self.cancel_button.grid(row=0, column=3, rowspan=2, sticky="ne", padx=(10, 0))

        self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate",
                                        maximum=100)
        self.progress.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(6, 4))

        ttk.Label(self, textvariable=self.detail_var, style="Muted.TLabel",
                  anchor="w").grid(row=2, column=1, sticky="w")
        right = ttk.Frame(self, style="Plain.TFrame")
        right.grid(row=2, column=2, sticky="e")
        ttk.Label(right, textvariable=self.percent_var, style="Muted.TLabel").pack(side="left")
        ttk.Label(right, textvariable=self.speed_var, style="Muted.TLabel").pack(side="left", padx=(10, 0))

        self.columnconfigure(1, weight=1)
        self._finished = False
        self._apply(status, progress)

    def _cancel(self):
        if self.on_cancel:
            self.cancel_button.state(["disabled"])
            self.detail_var.set("Đang hủy…")
            self.on_cancel(self.file_name)

    def _apply(self, status, progress):
        color, bar_style, icon = styles.status_kind(status)
        if styles.is_finished(status):
            self._finished = True
            self.cancel_button.grid_remove()   # tệp đã kết thúc -> ẩn nút Hủy
        elif self._finished and self.on_cancel:  # tệp được gửi lại sau khi đã kết thúc
            self._finished = False
            self.cancel_button.state(["!disabled"])
            self.cancel_button.grid()
        self.status_var.set(status)
        self.status_label.configure(fg=color)
        self.icon.configure(text=icon, fg=color)
        self.progress.configure(style=bar_style, value=progress)
        self.percent_var.set(f"{int(progress)}%")

    def update(self, status=None, progress=None, speed=None, detail=None):
        if status is not None or progress is not None:
            status = status if status is not None else self.status_var.get()
            progress = progress if progress is not None else self.progress_var.get()
            self.progress_var.set(progress)
            self._apply(status, progress)
        if speed is not None:
            self.speed_var.set(speed)
        if detail is not None:
            self.detail_var.set(detail)