import socket


def check_connection(host, port, timeout=30):
    
    with socket.create_connection((host, port), timeout=timeout):
        pass
