
import json
import queue
import socket
import struct
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tkinterdnd2 import DND_FILES, TkinterDnD


HOST = "127.0.0.1"
PORT = 65432
CHUNK_SIZE = 4096


class FileTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP File Transfer")
        self.root.geometry("620x520")
        self.root.minsize(540, 450)

        self.selected_file = None
        self.events = queue.Queue()
        self.uploading = False

        self.setup_style()
        self.build_ui()

        # Cập nhật giao diện từ hàng đợi sự kiện
        self.root.after(100, self.process_events)

    def setup_style(self):
        self.root.configure(bg="#F3F6FB")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Upload.Horizontal.TProgressbar",
            troughcolor="#DCE5F1",
            background="#3478F6",
            thickness=12
        )
        style.configure(
            "TButton",
            font=("Segoe UI", 10),
            padding=8
        )

    def build_ui(self):
        header = tk.Frame(self.root, bg="#F3F6FB")
        header.pack(fill="x", padx=28, pady=(22, 12))

        tk.Label(
            header,
            text="TCP File Transfer",
            font=("Segoe UI", 21, "bold"),
            fg="#172B4D",
            bg="#F3F6FB"
        ).pack(anchor="w")

        tk.Label(
            header,
            text=f"Server: {HOST}:{PORT}",
            font=("Segoe UI", 10),
            fg="#64748B",
            bg="#F3F6FB"
        ).pack(anchor="w", pady=(4, 0))

        # Vùng kéo thả file
        self.drop_area = tk.Frame(
            self.root,
            bg="white",
            highlightbackground="#8CB4F8",
            highlightthickness=2,
            height=175
        )
        self.drop_area.pack(fill="x", padx=28, pady=10)
        self.drop_area.pack_propagate(False)

        tk.Label(
            self.drop_area,
            text="⇧",
            font=("Segoe UI", 30),
            fg="#3478F6",
            bg="white"
        ).pack(pady=(12, 0))

        tk.Label(
            self.drop_area,
            text="Kéo thả file vào đây",
            font=("Segoe UI", 14, "bold"),
            fg="#172B4D",
            bg="white"
        ).pack()

        tk.Label(
            self.drop_area,
            text="Hoặc chọn file từ máy tính",
            font=("Segoe UI", 10),
            fg="#64748B",
            bg="white"
        ).pack(pady=4)

        ttk.Button(
            self.drop_area,
            text="Chọn file",
            command=self.choose_file
        ).pack(pady=(4, 10))

        # Cho phép kéo thả file vào vùng upload
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind("<<Drop>>", self.on_drop)

        # Thông tin file
        self.file_card = tk.Frame(
            self.root,
            bg="white",
            padx=16,
            pady=14
        )
        self.file_card.pack(fill="x", padx=28, pady=10)

        self.file_name_label = tk.Label(
            self.file_card,
            text="Chưa chọn file",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#172B4D",
            anchor="w"
        )
        self.file_name_label.pack(fill="x")

        self.file_size_label = tk.Label(
            self.file_card,
            text="Dung lượng: --",
            font=("Segoe UI", 9),
            bg="white",
            fg="#64748B",
            anchor="w"
        )
        self.file_size_label.pack(fill="x", pady=(4, 12))

        self.progress = ttk.Progressbar(
            self.file_card,
            style="Upload.Horizontal.TProgressbar",
            maximum=100,
            value=0
        )
        self.progress.pack(fill="x")

        self.progress_label = tk.Label(
            self.file_card,
            text="0%",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#3478F6",
            anchor="e"
        )
        self.progress_label.pack(fill="x", pady=(5, 0))

        # Trạng thái và nút gửi
        bottom = tk.Frame(self.root, bg="#F3F6FB")
        bottom.pack(fill="x", padx=28, pady=8)

        self.status_label = tk.Label(
            bottom,
            text="Sẵn sàng gửi file",
            font=("Segoe UI", 10),
            bg="#F3F6FB",
            fg="#64748B",
            anchor="w"
        )
        self.status_label.pack(fill="x", pady=(0, 10))

        self.upload_button = ttk.Button(
            bottom,
            text="Upload file lên Server",
            command=self.start_upload
        )
        self.upload_button.pack(fill="x")

    @staticmethod
    def format_size(size):
        units = ["B", "KB", "MB", "GB"]
        value = float(size)

        for unit in units:
            if value < 1024 or unit == "GB":
                return f"{value:.2f} {unit}"
            value /= 1024

        return f"{value:.2f} GB"

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Chọn file cần upload"
        )
        if path:
            self.set_file(path)

    def on_drop(self, event):
        # splitlist xử lý đường dẫn có khoảng trắng
        paths = self.root.tk.splitlist(event.data)

        if paths:
            self.set_file(paths[0])

    def set_file(self, path):
        if self.uploading:
            return

        path = Path(path)

        if not path.is_file():
            messagebox.showerror(
                "Lỗi",
                "Vui lòng chọn một file hợp lệ."
            )
            return

        self.selected_file = path
        self.file_name_label.config(text=path.name)
        self.file_size_label.config(
            text=f"Dung lượng: {self.format_size(path.stat().st_size)}"
        )
        self.progress["value"] = 0
        self.progress_label.config(text="0%")
        self.status_label.config(text="File đã sẵn sàng để upload")

    def start_upload(self):
        if self.uploading:
            return

        if self.selected_file is None:
            messagebox.showwarning(
                "Chưa chọn file",
                "Hãy kéo thả hoặc chọn file trước."
            )
            return

        if not self.selected_file.is_file():
            messagebox.showerror("Lỗi", "File không còn tồn tại.")
            return

        self.uploading = True
        self.upload_button.config(state="disabled")
        self.status_label.config(text="Đang kết nối tới Server...")
        self.progress["value"] = 0
        self.progress_label.config(text="0%")

        # Chạy mạng ở thread riêng để GUI không bị treo
        threading.Thread(
            target=self.upload_worker,
            args=(self.selected_file,),
            daemon=True
        ).start()

    def upload_worker(self, file_path):
        try:
            filesize = file_path.stat().st_size
            metadata = {
                "filename": file_path.name,
                "filesize": filesize
            }
            header = json.dumps(metadata).encode("utf-8")

            sent = 0
            started = time.monotonic()

            with socket.create_connection(
                (HOST, PORT), timeout=10
            ) as client:
                client.sendall(struct.pack("!I", len(header)))
                client.sendall(header)

                with file_path.open("rb") as f:
                    while True:
                        chunk = f.read(CHUNK_SIZE)

                        if not chunk:
                            break

                        client.sendall(chunk)
                        sent += len(chunk)

                        elapsed = max(
                            time.monotonic() - started, 0.001
                        )
                        speed = sent / elapsed

                        percent = (
                            100 if filesize == 0
                            else sent * 100 / filesize
                        )

                        self.events.put((
                            "progress", percent, sent,
                            filesize, speed
                        ))

                # Báo đã gửi hết byte trước khi chờ phản hồi
                client.settimeout(30)
                response = client.recv(1024).decode(
                    "utf-8", errors="replace"
                )

                if response.startswith("OK:"):
                    self.events.put(("success", response))
                else:
                    self.events.put((
                        "error",
                        response or "Server không xác nhận file."
                    ))

        except (OSError, ValueError) as exc:
            self.events.put(("error", str(exc)))

    def process_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]

                if kind == "progress":
                    _, percent, sent, total, speed = event

                    self.progress["value"] = percent
                    self.progress_label.config(
                        text=f"{percent:.1f}%"
                    )
                    self.status_label.config(
                        text=(
                            f"{self.format_size(sent)} / "
                            f"{self.format_size(total)}  •  "
                            f"{self.format_size(int(speed))}/s"
                        )
                    )

                elif kind == "success":
                    self.progress["value"] = 100
                    self.progress_label.config(text="100%")
                    self.status_label.config(
                        text="Upload thành công!"
                    )
                    messagebox.showinfo(
                        "Thành công", event[1]
                    )
                    self.uploading = False
                    self.upload_button.config(state="normal")

                elif kind == "error":
                    self.status_label.config(
                        text=f"Upload thất bại: {event[1]}"
                    )
                    messagebox.showerror(
                        "Lỗi upload", event[1]
                    )
                    self.uploading = False
                    self.upload_button.config(state="normal")

        except queue.Empty:
            pass

        self.root.after(100, self.process_events)


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = FileTransferApp(root)
    root.mainloop()