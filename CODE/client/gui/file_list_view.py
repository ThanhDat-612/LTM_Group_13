import tkinter as tk
from tkinter import ttk

from client.gui import styles
from client.gui.progress_item import ProgressItem


class FileListView(ttk.Frame):
    def __init__(self, master, on_cancel=None):
        super().__init__(master)
        self.on_cancel = on_cancel
        self.items = {}
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=styles.BG)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.container = ttk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=self.scroll.set)
        self._window = self.canvas.create_window((0, 0), window=self.container, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")

        self.empty = ttk.Label(self.container, text="Chưa có tệp nào.\nKéo thả hoặc chọn file để bắt đầu.",
                               style="Subtitle.TLabel", justify="center")
        self.empty.pack(pady=40, fill="x")

        self.container.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Enter>", lambda e: self._bind_wheel(True))
        self.canvas.bind("<Leave>", lambda e: self._bind_wheel(False))

    def _bind_wheel(self, on):
        if on:
            self.canvas.bind_all("<MouseWheel>", self._on_wheel)
            self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
            self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
        else:
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                self.canvas.unbind_all(seq)

    def _on_wheel(self, event):
        if self.container.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def _on_canvas_resize(self, event):
        self.canvas.itemconfigure(self._window, width=event.width)  # thẻ luôn rộng hết khung

    def _on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_or_update(self, file_name, status, progress, speed, detail=""):
        if file_name not in self.items:
            self.empty.pack_forget()
            widget = ProgressItem(self.container, file_name, status=status,
                                  progress=progress, speed=speed, detail=detail,
                                  on_cancel=self.on_cancel)
            widget.pack(fill="x", pady=(0, 8), padx=(0, 6))
            self.items[file_name] = widget
        else:
            self.items[file_name].update(status=status, progress=progress,
                                         speed=speed, detail=detail)
        self._on_configure(None)

    def clear(self):
        for widget in self.items.values():
            widget.destroy()
        self.items.clear()
        self.empty.pack(pady=40, fill="x")