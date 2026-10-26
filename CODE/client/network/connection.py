import socket

def check_connection(host, port, timeout=30):
    """Kiểm tra kết nối TCP đến server."""
    port = int(port)
    with socket.create_connection((host, port), timeout=timeout):
        return True

    return False


