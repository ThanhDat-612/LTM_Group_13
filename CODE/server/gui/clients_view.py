from tkinter import ttk

from server.gui import styles


class ClientsView(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, style="Plain.TFrame", **kwargs)
        self.tree = ttk.Treeview(self, columns=("address", "status"), show="headings",
                                 height=6, selectmode="browse")
        self.tree.heading("address", text="Client", anchor="w")
        self.tree.heading("status", text="Trạng thái", anchor="center")
        self.tree.column("address", width=170, anchor="w")
        self.tree.column("status", width=100, anchor="center")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        styles.configure_tree_tags(self.tree)

    def refresh(self, clients):
        ids = styles.unique_ids([str(c.get("address", "-")) for c in clients])
        rows = [(iid, (c.get("address", "-"), c.get("status", "-")),
                 styles.status_group(c.get("status", "")))
                for iid, c in zip(ids, clients)]
        styles.sync_tree(self.tree, rows)

    def selected_address(self):
        sel = self.tree.selection()
        return self.tree.item(sel[0], "values")[0] if sel else None