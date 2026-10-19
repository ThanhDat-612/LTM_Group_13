from tkinterdnd2 import TkinterDnD
from client.gui.main_window import FileTransferApp

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = FileTransferApp(root)
    root.mainloop()