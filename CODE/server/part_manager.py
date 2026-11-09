from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class UploadPaths:
    """Hai đường dẫn thuộc cùng một phiên nhận file."""

    final_path: Path
    temp_path: Path


class PartManager:
    def __init__(
        self,
        upload_dir: str | Path,
        reserve_file: Callable[[str, Path], Path],
    ) -> None:
        self.upload_dir = Path(upload_dir)
        self._reserve_file = reserve_file

    def reserve(self, filename: str) -> UploadPaths:
        """Giữ chỗ tên file đích và tạo ``.part`` độc quyền.

        Callback ``reserve_file`` của Server bảo vệ việc chọn và tạo file đích
        bằng khóa, tránh hai client ghi đè lên nhau khi upload đồng thời.
        """
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        final_path = Path(self._reserve_file(filename, self.upload_dir))
        temp_path = final_path.with_name(f".{final_path.name}.part")
        try:
            # 'xb' tránh vô tình ghi đè .part còn sót lại.
            with temp_path.open("xb"):
                pass
        except BaseException:
            # Nếu tạo .part thất bại, không để lại tệp giữ chỗ rỗng.
            self._remove_file(final_path)
            raise
        return UploadPaths(final_path=final_path, temp_path=temp_path)

    @staticmethod
    def commit(paths: UploadPaths, received: int, expected: int) -> Path:
        """Chỉ công bố file đích sau khi kiểm tra đủ byte và kích thước trên đĩa.

        Hàm được gọi SAU KHI đóng file .part để dữ liệu đã ghi hoàn tất.
        """
        if received != expected:
            raise ValueError(
                f"Dung lượng nhận được không khớp: mong đợi {expected}, thực tế {received}"
            )
        disk_size = paths.temp_path.stat().st_size
        if disk_size != expected:
            raise ValueError(
                f"Kích thước tệp tạm không khớp: mong đợi {expected}, thực tế {disk_size}"
            )
        os.replace(paths.temp_path, paths.final_path)
        return paths.final_path

    @staticmethod
    def discard(paths: UploadPaths) -> None:
        """Xóa file tạm và file giữ chỗ khi upload chưa commit thành công.

        Không gọi sau commit, vì lúc đó final_path đã là file hoàn chỉnh.
        """
        PartManager._remove_file(paths.temp_path)
        PartManager._remove_file(paths.final_path)

    @staticmethod
    def cleanup_stale(upload_dir: str | Path) -> int:
        """Xóa các ``.<tên>.part`` sót từ phiên cũ khi Server KHÔNG nhận file.

        Chỉ dùng khi khởi động Server; không gọi trong khi đang upload.
        """
        directory = Path(upload_dir)
        if not directory.is_dir():
            return 0
        removed = 0
        for path in directory.glob(".*.part"):
            if path.is_file() and not path.is_symlink():
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    pass
        return removed

    @staticmethod
    def _remove_file(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
