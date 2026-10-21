import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tkinterdnd2 import TkinterDnD
from client.gui.main_window import FileTransferApp

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = FileTransferApp(root)
    root.mainloop()