"""Secure one-file-per-connection upload handler.

Wire format: one UTF-8 JSON header terminated by newline, followed by exactly
`size` raw bytes. The server responds with one JSON line before and after data.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import time
from pathlib import Path

from server.security import SecurityManager


class UploadHandler:
    def __init__(self, client_socket, client_address, upload_dir="uploads", max_file_size_mb=500,
                 chunk_size=65536, timeout_seconds=30):
        self.client_socket = client_socket
        self.client_address = client_address
        self.upload_dir = Path(upload_dir).resolve()
        self.max_file_size_mb = max_file_size_mb
        self.chunk_size = max(1024, int(chunk_size))
        self.timeout_seconds = max(1, int(timeout_seconds))
        self.security = SecurityManager(max_file_size_mb)
        self.client_socket.settimeout(self.timeout_seconds)

    def _send_json(self, payload):
        self.client_socket.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))

    def _read_line(self, max_bytes=16384):
        data = bytearray()
        while len(data) < max_bytes:
            byte = self.client_socket.recv(1)
            if not byte:
                raise ConnectionError("Client disconnected before sending request header")
            if byte == b"\n":
                return bytes(data)
            data.extend(byte)
        raise ValueError("HEADER_TOO_LARGE: Request header exceeds allowed length")

    def _unique_destination(self, filename):
        destination = self.security.safe_destination(self.upload_dir, filename)
        if not destination.exists():
            return destination
        stem, suffix = destination.stem, destination.suffix
        stamp = time.strftime("%H%M-%d%m%Y")
        candidate = destination.with_name(f"{stem} {stamp}{suffix}")
        counter = 1
        while candidate.exists():
            candidate = destination.with_name(f"{stem} {stamp}-{counter}{suffix}")
            counter += 1
        return candidate

    def process(self):
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            raw_header = self._read_line()
            try:
                request = json.loads(raw_header.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json({"type": "ERROR", "code": "INVALID_HEADER", "message": "Header must be valid UTF-8 JSON."})
                return

            if not isinstance(request, dict) or request.get("type") != "UPLOAD_REQ":
                self._send_json({"type": "ERROR", "code": "INVALID_REQUEST", "message": "Expected UPLOAD_REQ."})
                return
            result = self.security.validate_upload_request(request)
            if not result:
                self._send_json({"type": "ERROR", **result.to_dict()})
                print(f"[SECURITY BLOCK] {self.client_address}: {result.code} - {result.message}")
                return

            filename = request["filename"]
            expected_size = int(request["size"])
            expected_checksum = request.get("checksum")
            destination = self._unique_destination(filename)
            temp_path = destination.with_name(destination.name + f".{os.getpid()}.{thread_id()}.part")
            self._send_json({"type": "UPLOAD_ACK", "accepted": True, "filename": destination.name})

            digest = hashlib.sha256()
            received = 0
            with open(temp_path, "xb") as output:
                while received < expected_size:
                    chunk = self.client_socket.recv(min(self.chunk_size, expected_size - received))
                    if not chunk:
                        raise ConnectionError(f"Incomplete upload: received {received}/{expected_size} bytes")
                    output.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)
                output.flush()
                os.fsync(output.fileno())

            size_result = self.security.validator.validate_received_size(expected_size, received)
            if not size_result:
                raise ValueError(f"{size_result.code}: {size_result.message}")
            if expected_checksum and digest.hexdigest().lower() != expected_checksum.lower():
                raise ValueError("CHECKSUM_MISMATCH: SHA-256 checksum does not match")

            # Atomic publish: incomplete or invalid files never get the final name.
            os.replace(temp_path, destination)
            temp_path = None
            self._send_json({"type": "RESULT", "success": True, "code": "OK",
                             "message": "Upload completed and verified.",
                             "filename": destination.name, "size": received,
                             "sha256": digest.hexdigest()})
            print(f"[UPLOAD OK] {self.client_address} -> {destination.name} ({received} bytes)")
        except (socket.timeout, ConnectionError, OSError, ValueError) as exc:
            message = str(exc)
            code = message.split(":", 1)[0] if ":" in message else "UPLOAD_FAILED"
            print(f"[UPLOAD REJECTED] {self.client_address}: {message}")
            try:
                self._send_json({"type": "RESULT", "success": False, "code": code, "message": message})
            except OSError:
                pass
        except Exception as exc:
            print(f"[UPLOAD ERROR] {self.client_address}: {exc}")
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass


def thread_id():
    import threading
    return threading.get_ident()
