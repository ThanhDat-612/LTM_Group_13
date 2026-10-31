from __future__ import annotations

# Ký tự cấm trên Windows (":" còn mở đường cho NTFS alternate data stream) + ký tự điều khiển
_INVALID_CHARS = set('<>:"|?*') | {chr(i) for i in range(32)}
_RESERVED = {"CON", "PRN", "AUX", "NUL",
             *(f"COM{i}" for i in range(1, 10)),
             *(f"LPT{i}" for i in range(1, 10))}
MAX_NAME_BYTES = 180   # chừa chỗ cho hậu tố ngày giờ khi đổi tên trùng và đuôi ".part"
TEMP_SUFFIX = ".part"


def validate_filename(filename: str) -> str:
    if not isinstance(filename, str):
        raise ValueError("Tên tập tin không hợp lệ")
    name = filename

    # Client chỉ gửi tên tệp, không bao giờ gửi đường dẫn -> từ chối thẳng thay vì tự cắt
    if "/" in name or "\\" in name:
        raise ValueError("Tên tập tin không được chứa đường dẫn")
    if not name or name in {".", ".."}:
        raise ValueError("Tên tập tin không hợp lệ")
    if name != name.strip() or name.endswith("."):
        raise ValueError("Tên tập tin không được bắt đầu/kết thúc bằng khoảng trắng hoặc dấu chấm")
    # Tên bắt đầu bằng "." hoặc kết thúc ".part" trùng với quy ước tệp tạm của server
    if name.startswith(".") or name.lower().endswith(TEMP_SUFFIX):
        raise ValueError("Tên tập tin không được bắt đầu bằng dấu chấm hoặc kết thúc bằng .part")
    if any(ch in _INVALID_CHARS for ch in name):
        raise ValueError("Tên tập tin chứa ký tự không được phép")
    if name.split(".")[0].strip().upper() in _RESERVED:
        raise ValueError("Tên tập tin là tên dành riêng của hệ điều hành")
    if len(name.encode("utf-8")) > MAX_NAME_BYTES:
        raise ValueError("Tên tập tin quá dài")
    return name