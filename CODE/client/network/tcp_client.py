
import socket
import json
import struct
from pathlib import Path

HOST = "127.0.0.1"
PORT = 65432
CHUNK_SIZE = 4096

# Thư mục chứa file cần gửi
SEND_DIR = Path(__file__).resolve().parent.parent / "send_files"


def send_file(file_path):
    file_path = Path(file_path)

    if not file_path.is_file():
        print(f"Không tìm thấy file: {file_path}")
        return

    # Tạo thông tin file
    metadata = {
        "filename": file_path.name,
        "filesize": file_path.stat().st_size
    }

    # Mã hóa metadata thành JSON
    header = json.dumps(metadata).encode("utf-8")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((HOST, PORT))
            print(f"Đã kết nối tới Server {HOST}:{PORT}")

            # Gửi độ dài header bằng 4 byte
            client.sendall(struct.pack("!I", len(header)))

            # Gửi metadata
            client.sendall(header)

            # Gửi nội dung file theo từng khối
            with file_path.open("rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)

                    if not chunk:
                        break

                    client.sendall(chunk)

            print(f"Đã gửi file: {file_path.name}")

            # Nhận phản hồi từ Server
            response = client.recv(1024)
            print("Server phản hồi:", response.decode("utf-8"))

    except OSError as e:
        print("Lỗi kết nối hoặc gửi file:", e)


if __name__ == "__main__":
    SEND_DIR.mkdir(parents=True, exist_ok=True)

    filename = input("Nhập tên file cần gửi: ").strip()
    file_path = SEND_DIR / filename

    send_file(file_path)