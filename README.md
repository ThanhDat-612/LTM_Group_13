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

- Kéo thả một hoặc nhiều file vào khu vực upload.
- Mỗi file có trạng thái riêng: **Chờ / Đang tải / Hoàn tất / Lỗi**.
- Hiển thị tốc độ và tiến trình upload cho từng file.
- Upload hàng đợi hoặc đồng thời, giới hạn tối đa **N file cùng lúc** (mặc định `N = 3`, chỉnh trong cấu hình).
- Lỗi của một file không làm dừng các file còn lại.
- Quy tắc trùng tên trên Server: tự động đổi tên theo ngày giờ `ten_file 2300-10072026.ext`, `ten_file 2315-11072026.ext`, ...
- Server kiểm tra dữ liệu từ Client, trả về lỗi rõ ràng khi dữ liệu không hợp lệ.
- Server ghi log: thời gian, kết nối, ngắt kết nối, lỗi, thao tác chính.
- GUI luôn hiển thị trạng thái kết nối và không bị treo khi upload.

## 3. Kiến trúc

- Mô hình: **Client–Server (TCP)**.
- Client và Server là hai tiến trình riêng, có thể chạy cùng máy hoặc khác máy.
- Mỗi file được upload qua một luồng/kết nối riêng để lỗi không lan sang file khác.
- File được ghi tạm dưới dạng `.part` trên Server, chỉ đổi tên thành file chính thức khi nhận đủ dữ liệu và kiểm tra hợp lệ.

```
+-----------+      TCP (IP:port cấu hình)      +-----------+
|  Client   | --------------------------------> |  Server   |
|  (GUI)    | <-------------------------------- | (threads) |
+-----------+       message + dữ liệu file      +-----------+
                                                      |
                                                 uploads/  +  logs/
```

## 4. Giao thức (tóm tắt)

> Chi tiết đầy đủ nằm trong báo cáo (thư mục `DOCX`).

| Bước | Hướng | Message | Nội dung chính |
|---|---|---|---|
| 1 | C → S | `UPLOAD_REQ` | tên file, kích thước, checksum |
| 2 | S → C | `UPLOAD_ACK` / `ERROR` | chấp nhận hoặc từ chối, tên file cuối cùng trên Server |
| 3 | C → S | `DATA` | các khối dữ liệu (chunk) |
| 4 | C → S | `UPLOAD_DONE` | báo kết thúc |
| 5 | S → C | `RESULT` | thành công hoặc mã lỗi |

- **Port mặc định:** `<ví dụ 5000>`
- **Mã lỗi:** `<liệt kê: tên file không hợp lệ, vượt dung lượng, dữ liệu sai, ...>`

## 5. Cấu hình

IP, port và các tham số không hard-code. Chỉnh trong file `Code/config.json`:

```json
{
  "server_host": "127.0.0.1",
  "server_port": 5000,
  "max_concurrent_uploads": 3,
  "chunk_size": 65536,
  "timeout_seconds": 30,
  "upload_dir": "uploads",
  "max_file_size_mb": 500
}
```
## 6. Cấu trúc dự án

```
udm10-multi-upload/
├── README.md
├── requirements.txt
├── config.json                # Cấu hình chung: host, port, max file, timeout...
│
├── docs/
│   ├── PROTOCOL.md            # Giao thức client <-> server
│   ├── ARCHITECTURE.md        # Kiến trúc, luồng upload
│   └── LIMITS.md              # Giới hạn số file upload đồng thời
│
├── common/                    # Code dùng chung 2 phía
│   ├── protocol.py            # Định nghĩa message, mã lệnh, mã lỗi
│   ├── constants.py           # Hằng số: chunk size, port, trạng thái file
│   └── utils.py               # Hàm tiện ích
│
├── server/
│   ├── main.py                # Khởi chạy server (GUI, hoặc --headless)
│   ├── server.py              # Lắng nghe kết nối, mỗi client/file một luồng
│   ├── upload_handler.py      # Nhận dữ liệu từng file, ghi vào .part
│   ├── part_manager.py        # Tạo/đổi tên/xoá file .part
│   ├── duplicate_policy.py    # Quy tắc xử lý trùng tên
│   ├── validator.py           # Kiểm tra tên file, kích thước, dữ liệu
│   ├── security.py            # Chống path traversal, giới hạn kết nối
│   ├── logger.py              # Ghi log ra file và đẩy sang GUI
│   ├── config_loader.py       # Đọc và kiểm tra config.json
│   ├── events.py              # Cầu nối server core <-> GUI (queue sự kiện)
│   ├── gui/                   # Giao diện server
│   │   ├── server_window.py   #   Cửa sổ chính, Start/Stop
│   │   ├── clients_view.py    #   Danh sách client đang kết nối
│   │   ├── uploads_view.py    #   File đang nhận: %, tốc độ, trạng thái
│   │   ├── log_view.py        #   Log realtime
│   │   ├── settings_panel.py  #   Chỉnh port, thư mục lưu, giới hạn
│   │   └── styles.py
│   ├── storage/
│   │   ├── uploads/           #   File hoàn tất
│   │   └── tmp/               #   File .part đang nhận
│   └── logs/
│
├── client/
│   ├── main.py                # Khởi chạy client
│   ├── models.py              # FileItem, enum trạng thái
│   ├── network/
│   │   ├── upload_manager.py  #   Điều phối hàng đợi và số file đồng thời
│   │   ├── upload_queue.py    #   Hàng đợi file chờ
│   │   ├── upload_worker.py   #   Luồng gửi 1 file
│   │   ├── speed_tracker.py   #   Tốc độ và % tiến trình
│   │   └── connection.py      #   Socket, timeout
│   └── gui/
│       ├── main_window.py
│       ├── drop_area.py       #   Khu vực kéo thả
│       ├── file_list_view.py  #   Danh sách file + trạng thái
│       ├── progress_item.py   #   Thanh tiến trình từng file
│       └── styles.py
│
├── tests/                     # Kiểm thử
│   ├── test_protocol.py
│   ├── test_duplicate.py
│   ├── test_validator.py
│   ├── test_concurrent.py
│   └── sample_files/
```
## 7. Cách chạy

```bash
pip install -r requirements.txt

# Server (có GUI)
python -m server.main

# Server không GUI (dùng khi test tự động)
python -m server.main --headless

# Client
python -m client.main
```

## 8. Kiểm thử

- Functional test cho toàn bộ chức năng bắt buộc.
- Test dữ liệu không hợp lệ (tên file sai, header lỗi, kích thước không khớp).
- Test ngắt kết nối đột ngột (Client hoặc Server).
- Stress và performance test với ít nhất hai mức tải khác nhau.
- Chỉ số đo: thời gian phản hồi, độ trễ, throughput, MB/giây, tỷ lệ lỗi, CPU, RAM.

Kết quả, cấu hình máy, dữ liệu đầu vào và bằng chứng nằm trong báo cáo và thư mục `Extra`.

## 9. Phân công

| STT | Họ tên | MSSV | Vai trò | Công việc |
|---|---|---|---|---|
| 1 | `<Trương Thành Đạt>` | `<079206016971>` | Leader | Kiến trúc, protocol, tích hợp, README |
| 2 | `<Nguyễn Hoàng An>` | `<056206010568>` | Server core | Nhận file, .part, xử lý trùng tên |
| 3 | `<Trần Nguyễn Du>` | `<080206009191>` | Server validation, log, bảo mật | Kiểm tra dữ liệu, log, cấu hình |
| 4 | `<Sử Quốc Duy>` | `<056206005633>` | Client network | Hàng đợi, đồng thời, tốc độ, timeout |
| 5 | `<Trần Minh Tuyền>` | `<056206005060>` | Client GUI | Kéo thả, trạng thái, tiến trình |
| 6 | `<Huỳnh Khánh Vân>` | `<072305001573>` | QA, demo, slide | Kiểm thử, video, PPTX |

## 11. Tài liệu

Document: https://docs.google.com/document/d/11_C4RPUITftiI3TEqs5c_iWzwgcEilVlQYWL_E85cD8/edit?usp=sharing

Tiến độ: https://docs.google.com/spreadsheets/d/1jIcIgjqGRsm7Z1z2i3sGU1-zjAeogrVH31qA5NgZrDM/edit?usp=sharing

Testcase: https://docs.google.com/spreadsheets/d/1jIcIgjqGRsm7Z1z2i3sGU1-zjAeogrVH31qA5NgZrDM/edit?gid=603698804#gid=603698804
