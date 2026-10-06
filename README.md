# UDM_10 --- Multi-File Upload System

## 1. Thông tin đề tài

-   **Project Code:** UDM_10
-   **Tên đề tài:** Upload nhiều file
-   **Ngôn ngữ:** Python
-   **GUI:** PySide6
-   **Network:** TCP Socket
-   **Mô hình:** Client -- Server
-   **Số thành viên:** 6
-   **Giới hạn upload đồng thời:** 2 file

## 2. Requirement bắt buộc

-   Kéo thả một hoặc nhiều file vào GUI.
-   Mỗi file có trạng thái riêng: `Waiting`, `Uploading`, `Completed`,
    `Error`.
-   Hiển thị progress riêng cho từng file.
-   Hiển thị tốc độ upload riêng cho từng file.
-   Có queue hoặc upload đồng thời.
-   Công bố giới hạn số file upload đồng thời: **2**.
-   Một file lỗi không được làm dừng các file còn lại.
-   Server có quy tắc xử lý file rõ ràng.
-   Không cần Pause/Resume vì thuộc UDM_12.

## 3. Công nghệ

### Client

-   Python 3.x
-   PySide6
-   socket
-   threading / ThreadPoolExecutor
-   pathlib
-   time

### Server

-   Python 3.x
-   socket
-   threading
-   pathlib
-   logging

### Quản lý mã nguồn

-   Git + GitHub
-   Mỗi thành viên làm branch riêng.
-   Không commit trực tiếp vào `main`.

## 4. Kiến trúc

``` text
                         TCP Socket
┌─────────────────────┐              ┌──────────────────────┐
│       CLIENT        │              │        SERVER        │
│                     │              │                      │
│     PySide6 GUI     │              │    TCP Listener      │
│         │           │              │          │           │
│         ▼           │              │          ▼           │
│   Upload Manager    │─────────────►│    Client Handler    │
│         │           │              │          │           │
│         ▼           │              │          ▼           │
│  Upload Task x N    │              │   File Receiver      │
│         │           │              │          │           │
│         ▼           │              │          ▼           │
│ TCP Client/Socket   │              │    File Manager      │
└─────────────────────┘              │          │           │
                                     │          ▼           │
                                     │      uploads/         │
                                     └──────────────────────┘
```

## 5. Bố cục thư mục

``` text
LTM/
│
├── CODE/
│   ├── client/
│   ├── server/
│   ├── storage/
│   └── tests/
│
├── DOCS/
│   ├── Report.docx
│   ├── System_Design.md
│   ├── Protocol.md
│   ├── Test_Plan.md
│   ├── Test_Results.md
│   └── User_Guide.md
│
├── EXTRA/
│   ├── sample_files/
│   ├── screenshots/
│   └── other_resources/
│
├── PPTX/
│   └── Presentation.pptx
│
└── README_UDM10.md
```

## 6. Protocol TCP

Nhóm phải thống nhất protocol trước khi code Client và Server.

Luồng cơ bản:

``` text
Client
  │
  ├── HEADER
  │     ├── Command = UPLOAD
  │     ├── Filename
  │     └── File size
  │
  ├── FILE DATA
  │     ├── Chunk 1
  │     ├── Chunk 2
  │     └── ...
  │
  └── END
        │
        ▼
      Server
```

File nên được đọc/gửi theo chunk, ví dụ **64 KB**, không đọc toàn bộ
file vào RAM.

## 7. Quy tắc Server

Nếu file trùng tên, không ghi đè.

Ví dụ:

``` text
report.pdf
report (1).pdf
report (2).pdf
```

Server chỉ được ghi file vào thư mục `storage/uploads/`.

## 8. Phân công 6 thành viên

### TV1 --- Team Lead / Architecture / Integration

-   Phân tích requirement.
-   Chốt kiến trúc.
-   Chốt TCP protocol.
-   Quản lý GitHub.
-   Review Pull Request.
-   Tích hợp code.
-   Chuẩn bị demo tổng thể.

### TV2 --- TCP Server

-   `server/main.py`
-   TCP Listener.
-   Accept Client.
-   `client_handler.py`.
-   Multi-client connection.
-   Disconnect/error handling.

### TV3 --- File Receiver / File Manager

-   `file_receiver.py`
-   `file_manager.py`
-   Nhận binary data.
-   Ghi file theo chunk.
-   Tạo storage.
-   Xử lý file trùng tên.
-   Xử lý lỗi file.

### TV4 --- Client Networking / Upload Manager

-   `tcp_client.py`
-   `upload_service.py`
-   `upload_manager.py`
-   Gửi header và file.
-   Queue.
-   Giới hạn 2 upload đồng thời.
-   Progress.
-   Speed.
-   Một file lỗi không làm file khác dừng.

### TV5 --- GUI / PySide6

-   `main_window.py`
-   Drag & Drop.
-   Chọn nhiều file.
-   Danh sách file.
-   Progress bar.
-   Speed.
-   Status.
-   Server connection status.

### TV6 --- Testing / Documentation / Demo

-   Thiết kế Test Case.
-   Chạy test.
-   Ghi Test Result.
-   Tạo file test.
-   Test lỗi mạng.
-   Test nhiều file.
-   Test concurrency.
-   Viết tài liệu.
-   Chuẩn bị slide và kịch bản demo.

**Tất cả thành viên vẫn phải test và review phần của mình.**

## 9. DOC nếu cần

Đề cương:

1.  Giới thiệu đề tài.
2.  Requirement.
3.  Công nghệ sử dụng.
4.  Kiến trúc Client--Server.
5.  Thiết kế TCP protocol.
6.  Thiết kế Client.
7.  Thiết kế Server.
8.  Cơ chế queue/concurrent upload.
9.  Progress và speed.
10. Error handling.
11. Test Case và kết quả.
12. Screenshot giao diện.
13. Kết quả đạt được.
14. Hạn chế.
15. Hướng phát triển.
16. Phân công thành viên.

## 10. Test Case