import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# LƯU Ý: Thêm dòng này để tránh lỗi chiếm dụng Port khi chạy lại
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind(('127.0.0.1', 65432))
server_socket.listen()

print("Server đang lắng nghe tại 127.0.0.1:65432...")

while True:
    conn, addr = server_socket.accept()
    print(f"Đã kết nối thành công từ: {addr}")
    
    data = conn.recv(1024)
    if data:
        print("Client gửi:", data.decode())
        conn.sendall(b"Hello client, server da nhan duoc tin nhan!")
    conn.close()