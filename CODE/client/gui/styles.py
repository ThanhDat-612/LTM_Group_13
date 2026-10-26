import tkinter as tk
from tkinter import ttk

# ---- Bảng màu ----
BG = "#f1f5f9"        # nền cửa sổ
CARD = "#ffffff"      # nền thẻ
BORDER = "#e2e8f0"
TEXT = "#0f172a"
MUTED = "#64748b"
PRIMARY = "#0d9488"   # teal
PRIMARY_DARK = "#0f766e"
PRIMARY_SOFT = "#ccfbf1"
INFO = "#2563eb"
SUCCESS = "#16a34a"
DANGER = "#dc2626"
WARN = "#d97706"

FONT = "Segoe UI"
F_BASE = (FONT, 10)
F_SMALL = (FONT, 9)
F_BOLD = (FONT, 10, "bold")
F_TITLE = (FONT, 16, "bold")
F_SECTION = (FONT, 11, "bold")


def status_group(status):
    """Phân nhóm trạng thái: 'cancel' | 'error' | 'done' | 'active' | 'wait'."""
    s = (status or "").lower()
    if any(k in s for k in ("hủy", "huy", "cancel")):
        return "cancel"
    if any(k in s for k in ("lỗi", "loi", "fail", "error", "thất bại")):
        return "error"
    if any(k in s for k in ("xong", "hoàn tất", "hoan tat", "done", "thành công", "complete")):
        return "done"
    if any(k in s for k in ("đang", "dang", "upload", "tải", "uploading")):
        return "active"
    return "wait"


def is_finished(status):
    return status_group(status) in ("cancel", "error", "done")


_KIND = {
    "cancel": (WARN, "Warn.Horizontal.TProgressbar", "⊘"),
    "error": (DANGER, "Danger.Horizontal.TProgressbar", "✕"),
    "done": (SUCCESS, "Success.Horizontal.TProgressbar", "✓"),
    "active": (INFO, "Info.Horizontal.TProgressbar", "↑"),
    "wait": (MUTED, "Muted.Horizontal.TProgressbar", "…"),
}


def status_kind(status):
    """Trả về (màu, tên style progressbar, biểu tượng) theo trạng thái."""
    return _KIND[status_group(status)]


def apply_styles(root):
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", font=F_BASE, background=BG, foreground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, relief="solid", borderwidth=1)
    style.configure("Plain.TFrame", background=CARD)

    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=CARD, foreground=TEXT)
    style.configure("Title.TLabel", background=BG, font=F_TITLE)
    style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=F_SMALL)
    style.configure("Section.TLabel", background=BG, font=F_SECTION)
    style.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=F_SMALL)
    style.configure("Status.TLabel", background=BG, foreground=MUTED, font=F_SMALL)
    style.configure("Ping.TLabel", background=PRIMARY_SOFT, foreground=PRIMARY_DARK,
                    font=F_BOLD, padding=(10, 3))

    style.configure("TEntry", fieldbackground=CARD, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=6)
    style.map("TEntry", bordercolor=[("focus", PRIMARY)], lightcolor=[("focus", PRIMARY)])

    style.configure("Primary.TButton", background=PRIMARY, foreground="white",
                    font=F_BOLD, padding=(16, 7), borderwidth=0, focusthickness=0)
    style.map("Primary.TButton",
              background=[("active", PRIMARY_DARK), ("pressed", PRIMARY_DARK)])
    style.configure("Secondary.TButton", background=CARD, foreground=TEXT,
                    font=F_BOLD, padding=(16, 7), bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, focusthickness=0)
    style.map("Secondary.TButton",
              background=[("active", BG)], bordercolor=[("active", PRIMARY)])

    style.configure("Danger.TButton", background=DANGER, foreground="white",
                    font=F_BOLD, padding=(16, 7), borderwidth=0, focusthickness=0)
    style.map("Danger.TButton", background=[("active", "#b91c1c"), ("pressed", "#b91c1c")])
    style.configure("Cancel.TButton", background=CARD, foreground=DANGER,
                    font=F_SMALL, padding=(10, 3), bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, focusthickness=0)
    style.map("Cancel.TButton", background=[("active", "#fef2f2")],
              bordercolor=[("active", DANGER)], foreground=[("disabled", "#cbd5e1")])

    style.configure("Vertical.TScrollbar", background=BORDER, troughcolor=BG,
                    bordercolor=BG, arrowsize=0, relief="flat")

    for name, color in (("Info", INFO), ("Success", SUCCESS),
                        ("Danger", DANGER), ("Warn", WARN), ("Muted", "#94a3b8")):
        style.configure(f"{name}.Horizontal.TProgressbar", background=color,
                        troughcolor=BORDER, bordercolor=BORDER,
                        lightcolor=color, darkcolor=color, thickness=8)
    return style