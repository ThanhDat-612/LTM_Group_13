import tkinter as tk

from client.gui import styles

try:
    from tkinterdnd2 import DND_FILES
except Exception:  # pragma: no cover
    DND_FILES = None

HINT = "Thả tệp vào đây hoặc nhấn để chọn file"


class DropArea(tk.Canvas):
    def __init__(self, master, callback=None, height=120, **kwargs):
        super().__init__(master, height=height, bg=styles.CARD, highlightthickness=0,
                         cursor="hand2", **kwargs)
        self.callback = callback
        self._hover = False
        self._text = HINT

        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))

        if DND_FILES is not None:
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind("<<Drop>>", self._drop_files)
                self.dnd_bind("<<DropEnter>>", lambda e: self._set_hover(True))
                self.dnd_bind("<<DropLeave>>", lambda e: self._set_hover(False))
            except Exception:
                pass

    def _set_hover(self, value):
        self._hover = value
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20:
            return
        color = styles.PRIMARY if self._hover else "#cbd5e1"
        fill = styles.PRIMARY_SOFT if self._hover else styles.CARD
        self.create_rectangle(3, 3, w - 3, h - 3, outline=color, fill=fill, width=2, dash=(6, 4))
        self.create_text(w / 2, h / 2 - 16, text="⬆", font=(styles.FONT, 22),
                         fill=styles.PRIMARY if self._hover else styles.MUTED)
        self.create_text(w / 2, h / 2 + 18, text=self._text, font=styles.F_BOLD,
                         fill=styles.TEXT)
        self.create_text(w / 2, h / 2 + 38, text="Hỗ trợ nhiều tệp  •  Ctrl+O để mở hộp thoại",
                         font=styles.F_SMALL, fill=styles.MUTED)

    def _click(self, event=None):
        if self.callback:
            self.callback()

    def _drop_files(self, event):
        self._set_hover(False)
        if not self.callback:
            return
        try:
            paths = list(self.tk.splitlist(event.data or ""))  # xử lý đúng {đường dẫn có khoảng trắng}
        except Exception:
            paths = []
        if paths:
            self.callback(paths)

    def set_text(self, text):
        self._text = text
        self._draw()