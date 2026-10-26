import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.server import Server

def main():
    print("=== Đang khởi động Server LTM Group 13 ===")

    # Khởi tạo và chạy server
    config_path = ROOT / "config.json"
    server = Server(config_path=str(config_path))
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[INFO] Đang dừng server theo yêu cầu từ bàn phím...")
        server.stop()

if __name__ == "__main__":
    main()


