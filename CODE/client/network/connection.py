
import socket


def check_connection(host, port, timeout=30):
    """Kiểm tra server có kết nối được không."""
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except (OSError, ValueError, TypeError):
        return False


def create_connection(host, port, timeout=30):
    """Tạo kết nối TCP và giữ socket mở."""
    return socket.create_connection((host, int(port)), timeout=timeout)


def close_connection(sock):
    """Đóng kết nối TCP."""
    if sock is not None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        finally:
            sock.close()
