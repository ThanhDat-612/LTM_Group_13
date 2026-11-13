import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.config_loader import ConfigError
from server.server import Server


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=== Đang khởi động Server LTM Group 13 ===")
    config_path = ROOT / "config.json"
    try:
        server = Server(config_path=str(config_path))
    except ConfigError as exc:
        print(f"[CONFIG ERROR] {exc}")
        sys.exit(1)

    try:
        import tkinter as tk
        from server.gui.server_window import ServerWindow

        root = tk.Tk()
        app = ServerWindow(root, server)
        app.pack(fill="both", expand=True)
        root.mainloop()
    except Exception as exc:
        print(f"[GUI ERROR] Không thể khởi chạy GUI server: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()