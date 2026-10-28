import json
import socket
import struct

MAX_JSON_FRAME = 1024 * 1024  # 1 MB, chặn khung JSON có độ dài bất thường


def _read_exact(sock: socket.socket, size: int) -> bytes:
    chunks = []
    received = 0
    while received < size:
        chunk = sock.recv(min(65536, size - received))
        if not chunk:
            raise EOFError("Socket closed before the full frame was received")
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)


def pack_json(payload: dict) -> bytes:
    """Đóng gói khung JSON: 4 byte độ dài + nội dung (dùng để gộp với dữ liệu khác)."""
    message = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return struct.pack(">I", len(message)) + message


def send_json(sock: socket.socket, payload: dict) -> None:
    sock.sendall(pack_json(payload))  # một lần gửi duy nhất


def recv_json(sock: socket.socket, chunk_size: int = 65536) -> dict:
    raw_length = _read_exact(sock, 4)
    length = struct.unpack(">I", raw_length)[0]
    if length > MAX_JSON_FRAME:
        raise ValueError(f"Khung JSON quá lớn ({length} byte)")
    raw = _read_exact(sock, length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def recv_exact(sock: socket.socket, size: int) -> bytes:
    return _read_exact(sock, size)


def send_chunk(sock: socket.socket, payload: bytes) -> None:
    sock.sendall(struct.pack(">I", len(payload)) + payload)