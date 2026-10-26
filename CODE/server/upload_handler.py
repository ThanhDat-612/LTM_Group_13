class UploadHandler:
    def __init__(self, client_socket, client_address):
        self.client_socket = client_socket
        self.client_address = client_address

    def process(self):
        """Xử lý quá trình nhận file, ghi file .part và xử lý trùng tên"""
        print(f"[UPLOAD HANDLER] Đang giao tiếp với client: {self.client_address}")
        try:
            while True:
                # Nhận dữ liệu từ client (tạm thời đọc luồng socket)
                data = self.client_socket.recv(4096)
                if not data:
                    break
                print(f"[DATA] Nhận được {len(bytes(data))} bytes từ {self.client_address}")
        except Exception as e:
            print(f"[ERROR] Lỗi trong quá trình xử lý upload của {self.client_address}: {e}")