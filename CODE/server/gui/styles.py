"""Style dùng chung với client (cùng bảng màu), thêm style cho Treeview và thẻ thống kê."""
import tkinter as tk
from tkinter import ttk

BG = "#f1f5f9"
CARD = "#ffffff"
BORDER = "#e2e8f0"
TEXT = "#0f172a"
MUTED = "#64748b"
PRIMARY = "#0d9488"
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
F_STAT = (FONT, 18, "bold")
F_MONO = ("Consolas", 9)


def status_group(status):
    """'cancel' | 'error' | 'done' | 'active' | 'wait' theo từ khoá trong chuỗi trạng thái."""
    s = (str(status) or "").lower()
    if any(k in s for k in ("hủy", "huy", "cancel", "ngắt", "ngat", "disconnect")):
        return "cancel"
    if any(k in s for k in ("lỗi", "loi", "fail", "error", "thất bại")):
        return "error"
    if any(k in s for k in ("xong", "hoàn tất", "hoan tat", "done", "thành công", "complete")):
        return "done"
    if any(k in s for k in ("đang", "dang", "upload", "tải", "nhận", "kết nối", "connected", "online")):
        return "active"
    return "wait"


GROUP_COLOR = {"cancel": WARN, "error": DANGER, "done": SUCCESS, "active": INFO, "wait": MUTED}


def configure_tree_tags(tree):
    for group, color in GROUP_COLOR.items():
        tree.tag_configure(group, foreground=color)


def sync_tree(tree, rows):
    """Cập nhật Treeview theo từng dòng (không xoá hết rồi chèn lại) để không nháy hình,
    giữ nguyên dòng đang chọn và vị trí cuộn. rows: list[(iid, values, tag)]."""
    wanted = [r[0] for r in rows]
    for iid in tree.get_children():
        if iid not in wanted:
            tree.delete(iid)
    for index, (iid, values, tag) in enumerate(rows):
        if tree.exists(iid):
            tree.item(iid, values=values, tags=(tag,))
            tree.move(iid, "", index)
        else:
            tree.insert("", index, iid=iid, values=values, tags=(tag,))


def unique_ids(keys):
    """Tạo iid không trùng từ danh sách khoá (khoá trùng được thêm hậu tố #n)."""
    seen, result = {}, []
    for key in keys:
        n = seen.get(key, 0)
        seen[key] = n + 1
        result.append(key if n == 0 else f"{key}#{n}")
    return result


def apply_styles(root):
    try:
        root.configure(bg=BG)
    except tk.TclError:
        pass
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
    style.configure("CardTitle.TLabel", background=CARD, font=F_SECTION)
    style.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=F_SMALL)
    style.configure("StatValue.TLabel", background=CARD, font=F_STAT)

    style.configure("TEntry", fieldbackground=CARD, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=6)
    style.map("TEntry", bordercolor=[("focus", PRIMARY)], lightcolor=[("focus", PRIMARY)],
              fieldbackground=[("disabled", BG)], foreground=[("disabled", MUTED)])
    style.configure("TCombobox", fieldbackground=CARD, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=6, arrowcolor=MUTED)
    style.map("TCombobox", fieldbackground=[("disabled", BG), ("readonly", CARD)],
              bordercolor=[("focus", PRIMARY)])

    for name, bg, hover, fg in (("Primary", PRIMARY, PRIMARY_DARK, "white"),
                                ("Danger", DANGER, "#b91c1c", "white")):
        style.configure(f"{name}.TButton", background=bg, foreground=fg, font=F_BOLD,
                        padding=(16, 7), borderwidth=0, focusthickness=0)
        style.map(f"{name}.TButton", background=[("active", hover), ("pressed", hover),
                                                 ("disabled", "#cbd5e1")])
    style.configure("Secondary.TButton", background=CARD, foreground=TEXT, font=F_BOLD,
                    padding=(14, 6), bordercolor=BORDER, lightcolor=BORDER,
                    darkcolor=BORDER, focusthickness=0)
    style.map("Secondary.TButton", background=[("active", BG)],
              bordercolor=[("active", PRIMARY)], foreground=[("disabled", "#94a3b8")])
    style.configure("Small.TButton", background=CARD, foreground=TEXT, font=F_SMALL,
                    padding=(10, 3), bordercolor=BORDER, lightcolor=BORDER,
                    darkcolor=BORDER, focusthickness=0)
    style.map("Small.TButton", background=[("active", BG)], bordercolor=[("active", PRIMARY)])

    style.configure("Vertical.TScrollbar", background=BORDER, troughcolor=CARD,
                    bordercolor=CARD, arrowsize=0, relief="flat")

    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                    rowheight=30, borderwidth=0, font=F_BASE)
    style.configure("Treeview.Heading", background=BG, foreground=MUTED, font=F_BOLD,
                    relief="flat", padding=(8, 6))
    style.map("Treeview", background=[("selected", PRIMARY_SOFT)],
              foreground=[("selected", TEXT)])
    style.map("Treeview.Heading", background=[("active", BORDER)])
    return style