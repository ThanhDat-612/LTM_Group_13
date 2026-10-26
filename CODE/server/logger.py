"""Ghi nhật ký hoạt động của server ra tệp.

Mỗi lần BẬT server tạo một tệp log mới (server_YYYYMMDD_HHMMSS.log) trong thư mục log,
ghi liên tục cho tới khi TẮT server rồi đóng tệp. Mỗi dòng được ghi xuống đĩa ngay nên
nếu chương trình bị tắt đột ngột thì vẫn không mất log.
"""
import threading
from datetime import datetime
from pathlib import Path


class SessionLogger:
    def __init__(self, log_dir, max_files=30):
        self.log_dir = Path(log_dir)
        self.max_files = max_files
        self.path = None
        self.last_error = None
        self._file = None
        self._lock = threading.Lock()

    @property
    def active(self):
        return self._file is not None

    def start(self, header=""):
        """Tạo tệp log cho phiên mới. Trả về đường dẫn; ném OSError nếu không tạo được."""
        with self._lock:
            self._close_locked()
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self._prune_locked()
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            n = 0
            while True:
                name = f"server_{stamp}.log" if n == 0 else f"server_{stamp}_{n}.log"
                try:
                    self._file = open(self.log_dir / name, "x", encoding="utf-8", buffering=1)  # ghi từng dòng
                    break
                except FileExistsError:
                    n += 1   # bật lại trong cùng một giây
            self.path = self.log_dir / name
            self.last_error = None
            if header:
                self._write_locked(header)
            return self.path

    def write(self, line):
        with self._lock:
            self._write_locked(line)

    def stop(self, footer=""):
        with self._lock:
            if footer:
                self._write_locked(footer)
            self._close_locked()

    # ---- nội bộ ----
    def _write_locked(self, line):
        if self._file is None:
            return
        try:
            self._file.write(line + "\n")
        except OSError as exc:   # đầy đĩa, mất quyền ghi... -> không để làm sập server
            self.last_error = str(exc)
            self._close_locked()

    def _close_locked(self):
        if self._file is not None:
            try:
                self._file.close()
            except OSError:
                pass
            self._file = None

    def _prune_locked(self):
        """Xoá bớt tệp log cũ, chỉ giữ max_files - 1 tệp (chừa chỗ cho tệp sắp tạo)."""
        if not self.max_files:
            return
        files = sorted(self.log_dir.glob("server_*.log"), key=lambda p: p.stat().st_mtime)
        for old in files[: max(len(files) - (self.max_files - 1), 0)]:
            try:
                old.unlink()
            except OSError:
                pass