
import socket
import json
import os

# Đọc cấu hình từ config.json nằm cùng thư mục
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# Lấy thông tin cấu hình
SERVER_HOST = config["server_host"]
SERVER_PORT = config["server_port"]
MAX_CONCURRENT_UPLOADS = config["max_concurrent_uploads"]
CHUNK_SIZE = config["chunk_size"]
TIMEOUT_SECONDS = config["timeout_seconds"]
UPLOAD_DIR = config["upload_dir"]
MAX_FILE_SIZE_MB = config["max_file_size_mb"]


def connect_to_server():
    # Tạo socket TCP
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Thiết lập thời gian chờ
    client.settimeout(TIMEOUT_SECONDS)

    try:
        # Kết nối đến Server
        client.connect((SERVER_HOST, SERVER_PORT))

        print(
            f"Đã kết nối tới Server "
            f"{SERVER_HOST}:{SERVER_PORT}"
        )

        return client

    except ConnectionRefusedError:
        print("Lỗi: Server chưa chạy hoặc chưa mở cổng kết nối.")

    except socket.timeout:
        print("Lỗi: Kết nối tới Server quá thời gian chờ.")

    except OSError as e:
        print(f"Lỗi kết nối: {e}")

    finally:
        # Chỉ đóng socket nếu kết nối chưa thành công
        # Socket thành công sẽ được trả về cho bên gọi hàm
        pass

    client.close()
    return None


if __name__ == "__main__":
    print("=== CẤU HÌNH CLIENT ===")
    print(f"Server host: {SERVER_HOST}")
    print(f"Server port: {SERVER_PORT}")
    print(f"Số upload đồng thời tối đa: {MAX_CONCURRENT_UPLOADS}")
    print(f"Kích thước mỗi khối dữ liệu: {CHUNK_SIZE} bytes")
    print(f"Thời gian chờ: {TIMEOUT_SECONDS} giây")
    print(f"Thư mục upload: {UPLOAD_DIR}")
    print(f"Dung lượng file tối đa: {MAX_FILE_SIZE_MB} MB")

    print("\n=== KẾT NỐI SERVER ===")
    sock = connect_to_server()

    if sock is not None:
        sock.close()
        print("Đã đóng kết nối kiểm tra.")
