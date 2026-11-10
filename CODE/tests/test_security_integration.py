import hashlib
import json
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.security import SecurityManager
from server.upload_handler import UploadHandler


class SecurityCoreTests(unittest.TestCase):
    def setUp(self):
        self.security = SecurityManager(1)

    def test_reject_path_traversal(self):
        self.assertFalse(self.security.validator.validate_filename("../evil.txt"))

    def test_reject_oversized_file(self):
        self.assertFalse(self.security.validator.validate_size(1024 * 1024 + 1))

    def test_reject_bad_checksum_format(self):
        result = self.security.validate_upload_request({"filename": "a.txt", "size": 1, "checksum": "xyz"})
        self.assertFalse(result)
        self.assertEqual(result.code, "INVALID_CHECKSUM")

    def test_server_rejects_path_traversal_before_ack(self):
        left, right = socket.socketpair()
        with tempfile.TemporaryDirectory() as tmp:
            request = {"type": "UPLOAD_REQ", "filename": "../outside.txt", "size": 1,
                       "checksum": hashlib.sha256(b"x").hexdigest()}
            thread = threading.Thread(target=UploadHandler(left, ("local", 2), tmp, 1, 1024, 3).process)
            thread.start()
            right.sendall((json.dumps(request) + "\n").encode())
            response = self._read_line(right)
            self.assertEqual(response["code"], "INVALID_FILENAME")
            self.assertFalse((Path(tmp).parent / "outside.txt").exists())
            thread.join(timeout=3)
        left.close(); right.close()

    def test_server_rejects_checksum_mismatch_and_removes_part(self):
        left, right = socket.socketpair()
        with tempfile.TemporaryDirectory() as tmp:
            payload = b"original bytes"
            request = {"type": "UPLOAD_REQ", "filename": "tampered.txt", "size": len(payload),
                       "checksum": hashlib.sha256(b"different bytes").hexdigest()}
            thread = threading.Thread(target=UploadHandler(left, ("local", 3), tmp, 1, 1024, 3).process)
            thread.start()
            right.sendall((json.dumps(request) + "\n").encode())
            self.assertEqual(self._read_line(right)["type"], "UPLOAD_ACK")
            right.sendall(payload)
            response = self._read_line(right)
            self.assertFalse(response["success"])
            self.assertEqual(response["code"], "CHECKSUM_MISMATCH")
            self.assertFalse((Path(tmp) / "tampered.txt").exists())
            self.assertEqual(list(Path(tmp).glob("*.part")), [])
            thread.join(timeout=3)
        left.close(); right.close()

    def test_server_uses_shared_security_core(self):
        left, right = socket.socketpair()
        with tempfile.TemporaryDirectory() as tmp:
            payload = b"hello security"
            request = {"type": "UPLOAD_REQ", "filename": "hello.txt", "size": len(payload),
                       "checksum": hashlib.sha256(payload).hexdigest()}
            thread = threading.Thread(target=UploadHandler(left, ("local", 1), tmp, 1, 1024, 3).process)
            thread.start()
            right.sendall((json.dumps(request) + "\n").encode())
            ack = self._read_line(right)
            self.assertEqual(ack["type"], "UPLOAD_ACK")
            right.sendall(payload)
            result = self._read_line(right)
            self.assertTrue(result["success"])
            self.assertEqual((Path(tmp) / "hello.txt").read_bytes(), payload)
            thread.join(timeout=3)
        left.close(); right.close()

    @staticmethod
    def _read_line(sock):
        data = bytearray()
        while True:
            byte = sock.recv(1)
            if byte == b"\n":
                return json.loads(data.decode())
            if not byte:
                raise AssertionError("socket closed before response")
            data.extend(byte)


if __name__ == "__main__":
    unittest.main()
