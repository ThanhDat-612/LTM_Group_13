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

## 9. Có cần DOC không?

**Nên làm.** Nếu thầy chưa nói rõ định dạng, nhóm nên chuẩn bị
`Report.docx` hoặc PDF.

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

Thầy yêu cầu testcase nên đây là phần **bắt buộc phải chuẩn bị nghiêm
túc**.

Mỗi testcase nên có:

  --------------------------------------------------------------------------
  ID          Test          Input        Expected    Actual      Status
                                         Result      Result      
  ----------- ------------- ------------ ----------- ----------- -----------
  TC01        Start Server  Start server Server                  
                                         listen port             
                                         5000                    

  TC02        Connect       Connect      Connected               
              Client                                             

  TC03        Upload 1 file 1 MB         Success                 

  TC04        Upload        5 files      All                     
              multiple                   uploaded                

  TC05        Concurrent    5 files      Max 2                   
              limit                      uploading               

  TC06        Progress      Large file   0 → 100%                

  TC07        Speed         Large file   Speed                   
                                         displayed               

  TC08        Duplicate     Same name    Auto rename             
              name          twice                                

  TC09        File error    Failed       Status =                
                            upload       Error                   

  TC10        Error         One file     Other files             
              isolation     fails        continue                

  TC11        Empty file    0-byte file  Defined                 
                                         behavior                

  TC12        Large file    500 MB+      Upload                  
                                         succeeds                

  TC13        Many files    10--20 files Queue works             

  TC14        Server        No server    Error                   
              unavailable                shown, app              
                                         does not                
                                         crash                   

  TC15        Network       Disconnect   Failed file             
              disconnect    during       handled                 
                            upload       correctly               
  --------------------------------------------------------------------------

### Test Case quan trọng nhất: TC10

Setup:

``` text
MAX_CONCURRENT = 2

A = good
B = intentionally fail
C = good
D = good
```

Expected:

``` text
A → Completed
B → Error
C → Completed
D → Completed
```

Không được để B lỗi khiến toàn bộ queue dừng.

## 11. Test concurrency

Với:

``` text
A B C D E
```

và:

``` text
MAX_CONCURRENT = 2
```

ban đầu:

``` text
A → Uploading
B → Uploading
C → Waiting
D → Waiting
E → Waiting
```

Sau khi A hoàn thành:

``` text
A → Completed
B → Uploading
C → Uploading
D → Waiting
E → Waiting
```

Tại mọi thời điểm:

``` text
Number of UPLOADING files <= 2
```

## 12. Test progress và speed

Nên dùng file:

``` text
100 MB
500 MB
1 GB
```

Kiểm tra:

-   Progress tăng từ 0 đến 100%.
-   Speed được cập nhật.
-   GUI không bị freeze.
-   Status chuyển đúng: `Waiting → Uploading → Completed`.

## 13. Test GUI

Kiểm tra:

-   Drag 1 file.
-   Drag nhiều file.
-   Hiển thị đúng tên và kích thước.
-   Progress cập nhật.
-   Speed cập nhật.
-   Status cập nhật.
-   GUI không freeze khi upload.

## 14. Git workflow

``` text
main
└── develop
     ├── feature/server
     ├── feature/file-manager
     ├── feature/client-upload
     ├── feature/gui
     ├── feature/testing
     └── feature/integration
```

Commit mẫu:

``` text
feat: implement TCP server
feat: implement file receiver
feat: add upload manager
feat: add concurrent upload limit
feat: add drag and drop
feat: add progress tracking
test: add multiple upload test cases
docs: update protocol documentation
fix: handle duplicate filenames
```

## 15. Thứ tự phát triển

``` text
1. Requirement + Protocol
          ↓
2. TCP Server + TCP Client
          ↓
3. Single File Upload
          ↓
4. Multiple File Upload
          ↓
5. Queue + Max 2 Concurrent
          ↓
6. Progress + Speed + Status
          ↓
7. GUI + Drag & Drop
          ↓
8. Error Handling
          ↓
9. Integration Test
          ↓
10. Documentation + Demo
```

Không nên để 6 thành viên code hoàn toàn độc lập rồi cuối cùng mới ghép.

## 16. MVP

Trước tiên phải đạt:

``` text
Client
  │
  │ TCP
  ▼
Server
  │
  ▼
storage/uploads/
```

Sau đó tăng dần:

``` text
1 file
  ↓
5 files
  ↓
2 concurrent uploads
  ↓
Progress
  ↓
Speed
  ↓
Status
  ↓
Drag & Drop
```

## 17. Không cần làm

Để tránh phạm vi quá lớn, không bắt buộc:

-   Login.
-   Database.
-   Cloud storage.
-   Web App.
-   Pause/Resume.
-   Encryption nâng cao.
-   User account.
-   Download.
-   File sharing.
-   Authentication.

## 18. Checklist cuối

### Requirement

-   [ ] Drag & Drop nhiều file.
-   [ ] Status riêng từng file.
-   [ ] Progress riêng từng file.
-   [ ] Speed riêng từng file.
-   [ ] Queue/concurrent.
-   [ ] Max concurrent = 2 được công bố.
-   [ ] Một file lỗi không ảnh hưởng file khác.
-   [ ] Server có quy tắc xử lý file.

### Code

-   [ ] Client chạy.
-   [ ] Server chạy.
-   [ ] TCP hoạt động.
-   [ ] Upload 1 file.
-   [ ] Upload nhiều file.
-   [ ] Concurrent upload.
-   [ ] Error handling.
-   [ ] GUI không freeze.

### Test

-   [ ] Single file.
-   [ ] Multiple files.
-   [ ] Concurrent limit.
-   [ ] Progress.
-   [ ] Speed.
-   [ ] Duplicate filename.
-   [ ] Error isolation.
-   [ ] Server unavailable.
-   [ ] Network disconnect.
-   [ ] Large file.
-   [ ] Many files.

### Documentation

-   [ ] README.md.
-   [ ] Report.docx/PDF.
-   [ ] Protocol documentation.
-   [ ] Test plan.
-   [ ] Test results.
-   [ ] Screenshots.
-   [ ] User guide.

### Demo

-   [ ] Start Server.
-   [ ] Start Client.
-   [ ] Connect.
-   [ ] Drag 5 files.
-   [ ] Show 2 files uploading simultaneously.
-   [ ] Show queue.
-   [ ] Show progress.
-   [ ] Show speed.
-   [ ] Demonstrate duplicate filename.
-   [ ] Demonstrate one file error while others continue.
-   [ ] Show files on Server.

## 19. Definition of Done

Một module chỉ được xem là hoàn thành khi:

-   [ ] Code chạy được.
-   [ ] Có test.
-   [ ] Không phá chức năng cũ.
-   [ ] Đã commit.
-   [ ] Đã push branch.
-   [ ] Đã tạo Pull Request.
-   [ ] Thành viên khác review.
-   [ ] Đã merge vào `develop`.

## 20. Mục tiêu sản phẩm cuối

Sản phẩm cuối phải thể hiện rõ:

``` text
TCP
+
File Transfer
+
Multiple Files
+
Queue/Concurrency
+
Progress
+
Speed
+
Independent Error Handling
+
PySide6 GUI
```

Ưu tiên hoàn thành **đúng requirement** trước, sau đó mới làm giao diện
đẹp và tính năng mở rộng.
