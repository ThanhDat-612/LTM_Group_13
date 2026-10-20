import sys
import os

# Đảm bảo Python nhận diện đường dẫn thư mục gốc
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.server import Server

def main():
    print("=== Đang khởi động Server LTM Group 13 ===")
    
    # Khởi tạo và chạy server
    server = Server(config_path="config.json")
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[INFO] Đang dừng server theo yêu cầu từ bàn phím...")
        server.stop()

if __name__ == "__main__":
    main()