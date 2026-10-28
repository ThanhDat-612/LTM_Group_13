import select
import socket
import threading
import time

from common.protocol import recv_json, send_json


class ClientSession(threading.Thread):
    """Giữ một kết nối điều khiển tới server trong suốt thời gian người dùng ở trạng thái "Đã kết nối".
    Server dựa vào kết nối này để biết client đang online; việc gửi tệp vẫn dùng kết nối riêng cho từng tệp."""

    def __init__(self, host, port, on_lost=None, on_ping=None, interval=15):
        super().__init__(daemon=True)
        self.host, self.port = host, int(port)
        self.on_lost = on_lost
        self.on_ping = on_ping
        self.interval = interval
        self._stop_event = threading.Event()
        self._sock = None

    def _ping(self):
        start = time.monotonic()
        send_json(self._sock, {"type": "PING"})
        reply = recv_json(self._sock)
        if reply.get("type") != "PONG":
            raise OSError("Phản hồi PING không hợp lệ")
        return round((time.monotonic() - start) * 1000, 1)

    def connect(self, timeout=3):
        """Kết nối, chào server và đo ping. Trả về ping (ms); ném OSError/EOFError/ValueError nếu thất bại."""
        sock = socket.create_connection((self.host, self.port), timeout=timeout)
        try:
            sock.settimeout(timeout)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._sock = sock
            send_json(sock, {"type": "HELLO"})
            if recv_json(sock).get("type") != "WELCOME":
                raise OSError("Server không phản hồi đúng giao thức")
            ping_ms = self._ping()
        except Exception:
            self._sock = None
            sock.close()
            raise
        self.start()
        return ping_ms

    def run(self):
        last_ping = time.monotonic()
        lost = False
        while not self._stop_event.wait(1.0):
            try:
                readable, _, _ = select.select([self._sock], [], [], 0)
                if readable and not self._sock.recv(1, socket.MSG_PEEK):
                    raise EOFError("Server đã đóng kết nối")   # phát hiện server tắt trong vòng ~1 giây
                if time.monotonic() - last_ping >= self.interval:
                    last_ping = time.monotonic()
                    ms = self._ping()
                    if self.on_ping:
                        self.on_ping(ms)
            except (OSError, EOFError, ValueError):
                lost = not self._stop_event.is_set()
                break
        self._close_socket()
        if lost and self.on_lost:
            self.on_lost()

    def _close_socket(self):
        sock, self._sock = self._sock, None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()

    def close(self):
        self._stop_event.set()