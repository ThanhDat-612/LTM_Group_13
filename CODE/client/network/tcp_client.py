import socket

# Khởi tạo Socket TCP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Kết nối tới Server (Phải trùng IP và Port với Server)
client_socket.connect(('127.0.0.1', 65432))

# Gửi dữ liệu
client_socket.sendall(b"Hello Server!")

# Nhận phản hồi
response = client_socket.recv(1024)
print("Server phản hồi:", response.decode())

client_socket.close()