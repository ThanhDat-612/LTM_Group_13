import queue
import tkinter as tk
from tkinter import filedialog, ttk

from server.gui import styles

MAX_LINES = 500


class LogView(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, style="Plain.TFrame", **kwargs)
        self.text = tk.Text(self, height=10, state="disabled", wrap="word", font=styles.F_MONO,
                            bg=styles.CARD, fg=styles.TEXT, relief="flat", borderwidth=0,
                            padx=6, pady=4, highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        for group, color in styles.GROUP_COLOR.items():
            self.text.tag_configure(group, foreground=color)
        self.text.tag_configure("wait", foreground=styles.TEXT)

        self._pending = queue.Queue()   # cho phép append() từ thread khác một cách an toàn
        self._shown = 0                 # số dòng của server.logs đã hiển thị (chế độ không có total)
        self._shown_total = 0           # tổng số dòng log server đã ghi mà giao diện đã hiển thị
        self.after(200, self._drain)

    # ---- thread-safe ----
    def append(self, message):
        self._pending.put(message)

    def _drain(self):
        try:
            while True:
                self._insert(self._pending.get_nowait())
        except queue.Empty:
            pass
        self.after(200, self._drain)

    # ---- hiển thị ----
    def _insert(self, message):
        at_bottom = self.text.yview()[1] >= 0.98
        self.text.configure(state="normal")
        self.text.insert("end", message + "\n", styles.status_group(message))
        lines = int(self.text.index("end-1c").split(".")[0])
        if lines > MAX_LINES:
            self.text.delete("1.0", f"{lines - MAX_LINES + 1}.0")
        if at_bottom:
            self.text.see("end")
        self.text.configure(state="disabled")

    def set_logs(self, logs, total=None):
        """Chỉ chèn thêm các dòng mới (không nháy, giữ vị trí cuộn).
        total: tổng số dòng server đã ghi từ trước đến nay (server.log_total). Cần khi server
        giới hạn độ dài danh sách log, vì lúc đó len(logs) không còn tăng nữa."""
        logs = list(logs)
        if total is None:
            if len(logs) < self._shown:      # log bị xoá -> làm lại từ đầu
                self._wipe()
            for item in logs[self._shown:]:
                self._insert(item)
            self._shown = len(logs)
            return
        new = total - self._shown_total
        if new < 0:                          # bộ đếm của server bị đặt lại
            self._wipe()
            new = len(logs)
        if new > 0:
            for item in logs[-new:]:
                self._insert(item)
        self._shown_total = total

    def _wipe(self, reset_counters=True):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
        if reset_counters:
            self._shown = 0
            self._shown_total = 0

    def clear(self):
        self._wipe(reset_counters=False)

    def save(self):
        path = filedialog.asksaveasfilename(title="Lưu log", defaultextension=".txt",
                                            filetypes=[("Văn bản", "*.txt"), ("Tất cả", "*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self.text.get("1.0", "end-1c"))