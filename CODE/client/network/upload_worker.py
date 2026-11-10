"""Small reference TCP uploader compatible with server.upload_handler."""
import hashlib
import json
import socket
from pathlib import Path


def _read_json_line(sock, limit=16384):
    data = bytearray()
    while len(data) < limit:
        byte = sock.recv(1)
        if not byte:
            raise ConnectionError("Server closed the connection")
        if byte == b"\n":
            return json.loads(data.decode("utf-8"))
        data.extend(byte)
    raise ValueError("Server response header too large")


def upload_file(host, port, file_path, timeout=30, chunk_size=65536):
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    request = {"type": "UPLOAD_REQ", "filename": path.name, "size": size,
               "checksum": digest.hexdigest()}
    with socket.create_connection((host, int(port)), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall((json.dumps(request) + "\n").encode("utf-8"))
        ack = _read_json_line(sock)
        if ack.get("type") != "UPLOAD_ACK" or not ack.get("accepted"):
            return ack
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(chunk_size), b""):
                sock.sendall(chunk)
        return _read_json_line(sock)
