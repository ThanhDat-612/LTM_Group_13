from tkinter import ttk

from server.gui import styles


class UploadsView(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, style="Plain.TFrame", **kwargs)
        self.tree = ttk.Treeview(self, columns=("file", "client", "progress", "speed", "status"),
                                 show="headings", height=8, selectmode="browse")
        for col, text, width, anchor in (("file", "Tệp", 200, "w"), ("client", "Client", 130, "w"),
                                         ("progress", "Tiến độ", 80, "center"),
                                         ("speed", "Tốc độ", 100, "center"),
                                         ("status", "Trạng thái", 100, "center")):
            self.tree.heading(col, text=text, anchor=anchor)
            self.tree.column(col, width=width, anchor=anchor, stretch=(col == "file"))
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        styles.configure_tree_tags(self.tree)

    def refresh(self, uploads):
        uploads = list(reversed(uploads))   # mới nhất ở trên cùng
        keys = [f"{u.get('client', '-')}|{u.get('file', '-')}" for u in uploads]
        rows = []
        for iid, u in zip(styles.unique_ids(keys), uploads):
            status = u.get("status", "chờ")
            progress = u.get("progress", 0)
            if isinstance(progress, (int, float)):
                progress = f"{int(progress)}%"
            rows.append((iid, (u.get("file", "-"), u.get("client", "-"), progress,
                               u.get("speed", "0 B/s"), status), styles.status_group(status)))
        styles.sync_tree(self.tree, rows)