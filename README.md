# UDM_10 — Upload nhiều file
 
| | |
|---|---|
| **Project Code** | UDM_10 |
| **Tên dự án** | Upload nhiều file |
| **Nhóm** | `NET_262701303_13` |
| **Giảng viên** | `Mai Ngọc Châu` |
| **Video demo** | `<Dán link YouTube Public/Unlisted tại đây>` |
 
## 1. Giới thiệu
 
Ứng dụng desktop (không phải Web App) gồm **Client GUI** và **Server**, giao tiếp qua mạng bằng TCP. Người dùng kéo thả một hoặc nhiều file vào GUI để upload lên Server. Mỗi file có trạng thái, tốc độ và tiến trình riêng.
 
## 2. Chức năng
 
- Kéo thả một hoặc nhiều file vào khu vực upload (`tkinterdnd2`).
- Mỗi file có trạng thái riêng: **Chờ / Đang tải / Hoàn tất / Lỗi** (thêm trạng thái **Đã hủy** khi người dùng hủy một file).
- Hiển thị tốc độ và tiến trình upload cho từng file.
- Upload hàng đợi kết hợp đồng thời, giới hạn tối đa **N file cùng lúc** (mặc định `N = 3`, chỉnh trong `config.json`). File vượt quá N nằm trong hàng đợi, khi một file kết thúc thì file kế tiếp được gửi.
- Lỗi của một file không làm dừng các file còn lại: mỗi file chạy trên một luồng và một kết nối TCP riêng.
- Hủy từng file hoặc hủy tất cả (file đang chờ thì gỡ khỏi hàng đợi, file đang gửi thì dừng worker). Không hỗ trợ Pause/Resume.
- Quy tắc trùng tên trên Server: tự động đổi tên theo ngày giờ, ví dụ `ten_file_10072026_230000.ext`; nếu vẫn trùng thì thêm `_1`, `_2`, ...
- Server kiểm tra dữ liệu từ Client (tên file, kích thước, dung lượng tối đa, dung lượng ổ đĩa, khung dữ liệu) và trả về lỗi rõ ràng khi không hợp lệ.
- Server ghi log: thời gian, kết nối, ngắt kết nối, lỗi, thao tác chính. Mỗi lần bật server tạo một file log mới.
- Client duy trì một kết nối điều khiển (HELLO, PING định kỳ 15 giây) để hiển thị trạng thái kết nối và độ trễ (ping), phát hiện server tắt trong khoảng 1 giây. GUI chạy độc lập với các luồng upload nên không bị treo.
## 3. Kiến trúc
 
- Mô hình: **Client–Server (TCP)**.
- Client và Server là hai tiến trình riêng, có thể chạy cùng máy hoặc khác máy.
- Server: một luồng `accept`, mỗi kết nối được xử lý bởi một luồng riêng (`UploadHandler`).
- Client: `UploadManager` điều phối `UploadQueue` (hàng đợi + tập file đang gửi), mỗi file do một `UploadWorker` (luồng) gửi qua kết nối riêng. `ClientSession` giữ kết nối điều khiển riêng để server biết client đang online.
- File được ghi tạm dưới dạng `.<tên_file>.part` ngay trong thư mục lưu trữ, chỉ đổi tên thành file chính thức (`os.replace`) khi nhận đủ dữ liệu và khớp kích thước. Lỗi hoặc ngắt kết nối thì xóa file tạm và file giữ chỗ. Khi bật server, các file `.part` còn sót từ lần chạy trước sẽ được dọn.
- Chống ghi chung một file: trước khi nhận, server chọn tên không trùng và giữ chỗ bằng cách tạo file rỗng ở chế độ `xb` (nguyên tử, có khóa).
```
+-----------+      TCP (IP:port cấu hình)      +-----------+
|  Client   | --------------------------------> |  Server   |
|  (GUI)    | <-------------------------------- | (threads) |
+-----------+       message + dữ liệu file      +-----------+
                                                      |
                                       server/storage/uploads  +  server/logs
```
 
## 4. Giao thức (tóm tắt)
 
Mỗi khung tin gồm **4 byte độ dài (big-endian)** + **nội dung JSON UTF-8** (tối đa 1 MB mỗi khung). Dữ liệu file gửi ngay sau khung `FILE_DATA` dưới dạng byte thô có độ dài bằng trường `size`.
 
**Kết nối điều khiển (một kết nối cho mỗi client đang online):**
 
| Hướng | Message | Nội dung |
|---|---|---|
| C → S | `HELLO` | đăng ký phiên client |
| S → C | `WELCOME` | `status: ok` |
| C → S | `PING` (mỗi 15 giây) | đo độ trễ, giữ kết nối |
| S → C | `PONG` | `status: ok` |
 
**Upload một file (mỗi file một kết nối riêng):**
 
| Bước | Hướng | Message | Nội dung chính |
|---|---|---|---|
| 1 | C → S | `UPLOAD_REQUEST` | `filename`, `size` |
| 2 | S → C | `UPLOAD_ACK` / `UPLOAD_ERROR` | `status: accepted` + `final_name` (tên cuối cùng trên Server), hoặc `message` lỗi |
| 3 | C → S | `FILE_DATA` | `size` của khối, theo sau là dữ liệu khối (mặc định 64 KB), lặp lại |
| 4 | C → S | `UPLOAD_DONE` | báo kết thúc |
| 5 | S → C | `UPLOAD_RESULT` | `status: success` + `final_name`, hoặc `status: error` + `message` |
 
Server xác nhận tính toàn vẹn bằng cách so sánh tổng số byte nhận được với `size` đã khai báo.
 
- **Port mặc định:** `5000`
- **Các lỗi Server trả về (`message`):**
  - Thiếu hoặc sai dung lượng tệp.
  - Tên tập tin không hợp lệ: chứa đường dẫn (`/`, `\`), rỗng hoặc `.`/`..`, bắt đầu/kết thúc bằng khoảng trắng hoặc dấu chấm, bắt đầu bằng `.` hoặc kết thúc `.part`, chứa ký tự cấm (`< > : " | ? *` và ký tự điều khiển), trùng tên dành riêng của hệ điều hành (CON, PRN, COM1...), quá dài (> 180 byte).
  - Tệp vượt quá dung lượng tối đa (`max_file_size_mb`).
  - Server không đủ dung lượng ổ đĩa (chừa tối thiểu 50 MB).
  - Server không tạo được tệp.
  - Loại tin nhắn dữ liệu không hợp lệ.
  - Khối dữ liệu quá lớn (> 4 MB).
  - Client gửi vượt quá dung lượng đã khai báo.
  - Dung lượng nhận được không khớp.
  - Quá thời gian chờ dữ liệu từ client (300 giây không có dữ liệu).
## 5. Cấu hình
 
IP, port và các tham số không hard-code. Chỉnh trong file `config.json` ở thư mục gốc dự án:
 
```json
{
  "server_host": "127.0.0.1",
  "server_port": 5000,
  "upload_dir": "server/storage/uploads",
  "log_dir": "server/logs",
  "stop_password": "admin123",
  "max_file_size_mb": 0,
  "max_log_files": 30,
 
  "max_concurrent_uploads": 3,
  "chunk_size": 65536,
  "timeout_seconds": 30
}
```
 
| Khóa | Ý nghĩa |
|---|---|
| `server_host`, `server_port` | Địa chỉ và cổng của Server |
| `upload_dir` | Thư mục lưu file hoàn tất (tính từ thư mục chứa `config.json`) |
| `log_dir` | Thư mục lưu file log |
| `stop_password` | Mật khẩu dùng khi dừng server |
| `max_file_size_mb` | Dung lượng tối đa mỗi file, `0` = không giới hạn |
| `max_log_files` | Số file log giữ lại, `0` = giữ tất cả |
| `max_concurrent_uploads` | Số file upload đồng thời tối đa (phía Client) |
| `chunk_size` | Kích thước khối dữ liệu (byte) |
| `timeout_seconds` | Thời gian chờ (giây) |
 
Thiếu khóa thì dùng giá trị mặc định; sai giá trị thì Server báo lỗi rõ ràng và không khởi động.
 
## 6. Cấu trúc dự án
 
```
udm10-multi-upload/
├── README.md
├── requirements.txt
├── config.json                # Cấu hình chung: host, port, giới hạn, log...
│
├── common/                    # Code dùng chung 2 phía
│   ├── protocol.py            # Đóng/đọc khung JSON + khối dữ liệu
│   ├── constants.py           # Hằng số: chunk size, port, trạng thái, tên message
│   └── utils.py               # Định dạng dung lượng/tốc độ, thời gian, tạo thư mục
│
├── server/
│   ├── main.py                # Khởi chạy server (GUI, hoặc --headless)
│   ├── server.py              # Lắng nghe kết nối, mỗi kết nối một luồng, bảng upload, log
│   ├── upload_handler.py      # Nhận dữ liệu từng file, ghi .part rồi đổi tên
│   ├── part_manager.py        # (chưa dùng) logic .part hiện nằm trong upload_handler.py
│   ├── duplicate_policy.py    # Quy tắc xử lý trùng tên
│   ├── validator.py           # Kiểm tra tên file
│   ├── security.py            # Hàm chống path traversal, giới hạn kết nối (chưa tích hợp)
│   ├── logger.py              # Ghi log ra file theo phiên
│   ├── config_loader.py       # Đọc và kiểm tra config.json
│   ├── gui/                   # Giao diện server
│   │   ├── server_window.py   #   Cửa sổ chính, Start/Stop
│   │   ├── clients_view.py    #   Danh sách client đang kết nối
│   │   ├── uploads_view.py    #   File đang nhận: %, tốc độ, trạng thái
│   │   ├── log_view.py        #   Log realtime
│   │   ├── settings_panel.py  #   Chỉnh port, thư mục lưu, giới hạn
│   │   └── styles.py
│   ├── logs/                  # File log
│   └── storage/               # File hoàn tất (uploads/)
│
├── client/
│   ├── main.py                # Khởi chạy client
│   ├── model.py               # FileItem, FileStatus
│   ├── models.py              # Re-export từ model.py
│   ├── network/
│   │   ├── upload_manager.py  #   Điều phối hàng đợi, số file đồng thời, hủy
│   │   ├── upload_queue.py    #   Hàng đợi file chờ + tập file đang gửi
│   │   ├── upload_worker.py   #   Luồng gửi 1 file
│   │   ├── speed_tracker.py   #   Tốc độ và % tiến trình
│   │   ├── session.py         #   Kết nối điều khiển (HELLO, PING)
│   │   └── connection.py      #   Kiểm tra kết nối, đo ping
│   └── gui/                   # Giao diện client (kéo thả, danh sách file, tiến trình)
│       ├── main_window.py
│       ├── drop_area.py       #   Khu vực kéo thả
│       ├── file_list_view.py  #   Danh sách file + trạng thái
│       ├── progress_item.py   #   Thanh tiến trình từng file
│       └── styles.py
└── tests/                     # Kiểm thử
```
 
## 7. Cách chạy
 
```bash
pip install -r requirements.txt   # cần tkinterdnd2 cho kéo thả
 
# Server (có GUI)
python -m server.main
 
# Server không GUI (dùng khi test tự động)
python -m server.main --headless
 
# Client
python -m client.main
```
 
## 8. Kiểm thử
 
Kế hoạch kiểm thử:
 
- Functional test cho toàn bộ chức năng bắt buộc.
- Test dữ liệu không hợp lệ (tên file sai, header lỗi, kích thước không khớp).
- Test ngắt kết nối đột ngột (Client hoặc Server).
- Stress và performance test với ít nhất hai mức tải khác nhau.
- Chỉ số đo: thời gian phản hồi, độ trễ, throughput, MB/giây, tỷ lệ lỗi, CPU, RAM.
Kết quả, cấu hình máy, dữ liệu đầu vào và bằng chứng nằm trong báo cáo.
 
## 9. Phân công
 
| STT | Họ tên | MSSV | Vai trò | Công việc |
|---|---|---|---|---|
| 1 | Trương Thành Đạt | 079206016971 | Leader | Kiến trúc, protocol, tích hợp, README |
| 2 | Nguyễn Hoàng An | 056206010568 | Server core | Nhận file, .part, xử lý trùng tên |
| 3 | Trần Nguyễn Du | 080206009191 | Server validation, log, bảo mật | Kiểm tra dữ liệu, log, cấu hình |
| 4 | Sử Quốc Duy | 056206005633 | Client network | Hàng đợi, đồng thời, tốc độ, timeout |
| 5 | Trần Minh Tuyển | 056206005060 | Client GUI | Kéo thả, trạng thái, tiến trình |
| 6 | Huỳnh Khánh Vân | 072305001573 | QA, demo, slide | Kiểm thử, video, PPTX |
 
## 10. Tài liệu
 
Document: https://docs.google.com/document/d/11_C4RPUITftiI3TEqs5c_iWzwgcEilVlQYWL_E85cD8/edit?usp=sharing
 
Tiến độ: https://docs.google.com/spreadsheets/d/1jIcIgjqGRsm7Z1z2i3sGU1-zjAeogrVH31qA5NgZrDM/edit?usp=sharing
 
Testcase: https://docs.google.com/spreadsheets/d/1jIcIgjqGRsm7Z1z2i3sGU1-zjAeogrVH31qA5NgZrDM/edit?gid=603698804#gid=603698804