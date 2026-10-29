import socket


def check_connection(host, port, timeout=30):
    """Kiểm tra kết nối TCP đến server."""
    try:
        port = int(port)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
    return False


def ping_server(host, port, timeout=2):
    try:
        port = int(port)
        start = __import__("time").time()
        with socket.create_connection((host, port), timeout=timeout):
            elapsed_ms = ( __import__("time").time() - start ) * 1000
            return round(elapsed_ms, 1)
    except OSError:
        return None


