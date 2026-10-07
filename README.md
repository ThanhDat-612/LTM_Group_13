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

## 6. Yêu cầu môi trường

- `<Python 3.10+>` 
- Thư viện: `<PyQt6 / tkinterdnd2 / ...>` — cài bằng `pip install -r requirements.txt`

## 7. Hướng dẫn chạy

**Chạy Server:**

```bash
cd Code
python server.py
```

**Chạy Client (cùng máy hoặc máy khác):**

```bash
cd Code
python client.py
```

Nếu chạy khác máy, sửa `server_host` trong `config.json` thành IP của máy chạy Server.

## 8. Cấu trúc thư mục

```
UDM_10/
├── Code/        # Mã nguồn Client và Server
├── DOCX/        # Báo cáo (Word)
├── Extra/       # Ảnh, video, bằng chứng kiểm thử, thông tin bổ sung
├── PPTX/        # Slide thuyết trình
└── ReadMe.md
```

## 9. Kiểm thử

- Functional test cho toàn bộ chức năng bắt buộc.
- Test dữ liệu không hợp lệ (tên file sai, header lỗi, kích thước không khớp).
- Test ngắt kết nối đột ngột (Client hoặc Server).
- Stress và performance test với ít nhất hai mức tải khác nhau.
- Chỉ số đo: thời gian phản hồi, độ trễ, throughput, MB/giây, tỷ lệ lỗi, CPU, RAM.

Kết quả, cấu hình máy, dữ liệu đầu vào và bằng chứng nằm trong báo cáo và thư mục `Extra`.

## 10. Phân công

| STT | Họ tên | MSSV | Vai trò | Công việc |
|---|---|---|---|---|
| 1 | `<Trương Thành Đạt>` | `<079206016971>` | Leader | Kiến trúc, protocol, tích hợp, README |
| 2 | `<>` | `<MSSV>` | Server core | Nhận file, .part, xử lý trùng tên |
| 3 | `<>` | `<MSSV>` | Server validation, log, bảo mật | Kiểm tra dữ liệu, log, cấu hình |
| 4 | `<>` | `<MSSV>` | Client network | Hàng đợi, đồng thời, tốc độ, timeout |
| 5 | `<>` | `<MSSV>` | Client GUI | Kéo thả, trạng thái, tiến trình |
| 6 | `<>` | `<MSSV>` | QA, demo, slide | Kiểm thử, video, PPTX |

## 11. Tài liệu

Document: https://docs.google.com/document/d/11_C4RPUITftiI3TEqs5c_iWzwgcEilVlQYWL_E85cD8/edit?usp=sharing

Tiến độ: https://docs.google.com/spreadsheets/d/1jIcIgjqGRsm7Z1z2i3sGU1-zjAeogrVH31qA5NgZrDM/edit?usp=sharing
Testcase: https://docs.google.com/spreadsheets/d/1jIcIgjqGRsm7Z1z2i3sGU1-zjAeogrVH31qA5NgZrDM/edit?gid=603698804#gid=603698804
