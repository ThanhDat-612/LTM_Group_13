
import socket
import json
import struct
from pathlib import Path

HOST = "127.0.0.1"
PORT = 65432
CHUNK_SIZE = 4096

# Thư mục lưu file nhận được
RECEIVED_DIR = Path(__file__).resolve().parent / "received_files"


def recv_exact(conn, size):
    """Nhận chính xác size byte từ TCP socket."""
    data = bytearray()

    while len(data) < size:
        chunk = conn.recv(min(CHUNK_SIZE, size - len(data)))

        if not chunk:
            raise ConnectionError("Client ngắt kết nối khi đang truyền dữ liệu.")

        data.extend(chunk)

    return bytes(data)


def receive_file(conn):
    # Nhận độ dài header (4 byte)
    raw_length = recv_exact(conn, 4)
    header_length = struct.unpack("!I", raw_length)[0]

    # Giới hạn kích thước metadata để tránh cấp phát quá lớn
    if not 1 <= header_length <= 65536:
        raise ValueError("Độ dài metadata không hợp lệ.")

    # Nhận và giải mã metadata
    metadata = json.loads(
        recv_exact(conn, header_length).decode("utf-8")
    )

    filename = metadata["filename"]
    filesize = metadata["filesize"]

    # Chỉ lấy tên file, không cho phép đường dẫn từ Client
    filename = Path(filename).name

    if not filename or filename in (".", ".."):
        raise ValueError("Tên file không hợp lệ.")

    if type(filesize) is not int or filesize < 0:
        raise ValueError("Kích thước file không hợp lệ.")

    RECEIVED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RECEIVED_DIR / filename

    # Nhận đúng số byte mà Client đã khai báo
    with output_path.open("wb") as f:
        remaining = filesize

        while remaining > 0:
            chunk = conn.recv(min(CHUNK_SIZE, remaining))

            if not chunk:
                raise ConnectionError(
                    "Client ngắt kết nối trước khi gửi đủ file."
                )

            f.write(chunk)
            remaining -= len(chunk)

    print(f"Nhận file thành công: {filename} ({filesize} bytes)")
    conn.sendall(f"OK: Đã nhận file {filename}".encode("utf-8"))


def main():
    RECEIVED_DIR.mkdir(parents=True, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()

        print(f"Server đang lắng nghe tại {HOST}:{PORT}...")

        while True:
            conn, addr = server.accept()

            with conn:
                print(f"Client kết nối: {addr}")

                try:
                    receive_file(conn)
                except (OSError, ValueError, KeyError,
                        UnicodeDecodeError, json.JSONDecodeError) as e:
                    print("Lỗi nhận file:", e)
                except ConnectionError as e:
                    print("Lỗi kết nối:", e)
                finally:
                    print("Kết thúc phiên truyền file.")


if __name__ == "__main__":
    main()