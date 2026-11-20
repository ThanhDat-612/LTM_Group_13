"""Đọc và kiểm tra config.json. Tất cả giá trị phải đọc trực tiếp từ file cấu hình."""
import json
from dataclasses import dataclass, field
from pathlib import Path

REQUIRED_KEYS = {
    "server_host",
    "server_port",
    "upload_dir",
    "log_dir",
    "stop_password",
    "max_file_size_mb",
    "max_log_files",
    "max_concurrent_uploads",
    "chunk_size",
    "timeout_seconds",
}
# Các khoá dùng chung giữa client và server; nếu có mặt trong config.json thì được đọc và áp dụng.
SHARED_KEYS = {"max_concurrent_uploads", "chunk_size", "timeout_seconds"}
# Tên khoá cũ vẫn được chấp nhận
ALIASES = {"host": "server_host", "port": "server_port"}


class ConfigError(Exception):
    """config.json không hợp lệ. Thông báo đã viết sẵn cho người dùng đọc."""


@dataclass
class ServerConfig:
    path: Path
    host: str
    port: int
    upload_dir: Path
    log_dir: Path
    stop_password: str
    max_file_size_mb: int
    max_log_files: int
    max_concurrent_uploads: int
    chunk_size: int
    timeout_seconds: int
    warnings: list = field(default_factory=list)   # ví dụ: khoá lạ trong file cấu hình


def find_config_path(config_path="config.json"):
    path = Path(config_path)
    if path.is_absolute():
        return path
    candidates = [
        Path(__file__).resolve().parent.parent / path,
        Path.cwd() / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _as_int(name, value, minimum, maximum=None):
    if isinstance(value, bool):
        raise ConfigError(f'"{name}" phải là số nguyên, không phải true/false')
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ConfigError(f'"{name}" phải là số nguyên (hiện là {value!r})')
    if number < minimum or (maximum is not None and number > maximum):
        limit = f"từ {minimum} đến {maximum}" if maximum is not None else f"từ {minimum} trở lên"
        raise ConfigError(f'"{name}" phải {limit} (hiện là {number})')
    return number


def _as_text(name, value):
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f'"{name}" phải là chuỗi không rỗng (hiện là {value!r})')
    return value.strip()


def load_config(config_path="config.json"):
    path = find_config_path(config_path)
    if not path.exists():
        raise ConfigError(f"Không tìm thấy tệp cấu hình: {path}")

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path.name} không phải JSON hợp lệ: {exc.msg} (dòng {exc.lineno}, cột {exc.colno})")
    except OSError as exc:
        raise ConfigError(f"Không đọc được {path}: {exc}")

    if not isinstance(raw, dict):
        raise ConfigError(f"{path.name} phải là một đối tượng JSON {{...}}")

    data = {}
    warnings = []
    for key, value in raw.items():
        key = ALIASES.get(key, key)
        data[key] = value

    missing = sorted(key for key in REQUIRED_KEYS if key not in data)
    if missing:
        raise ConfigError(f"Thiếu trường bắt buộc trong {path.name}: {', '.join(missing)}")

    for key in sorted(data):
        if key not in REQUIRED_KEYS and key not in SHARED_KEYS:
            warnings.append(f'Khoá không dùng trong {path.name}: "{key}"')

    base = path.resolve().parent
    return ServerConfig(
        path=path,
        host=_as_text("server_host", data["server_host"]),
        port=_as_int("server_port", data["server_port"], 1, 65535),
        upload_dir=(base / _as_text("upload_dir", data["upload_dir"])).resolve(),
        log_dir=(base / _as_text("log_dir", data["log_dir"])).resolve(),
        stop_password=_as_text("stop_password", data["stop_password"]),
        max_file_size_mb=_as_int("max_file_size_mb", data["max_file_size_mb"], 0),
        max_log_files=_as_int("max_log_files", data["max_log_files"], 0),
        max_concurrent_uploads=_as_int("max_concurrent_uploads", data["max_concurrent_uploads"], 1),
        chunk_size=_as_int("chunk_size", data["chunk_size"], 1),
        timeout_seconds=_as_int("timeout_seconds", data["timeout_seconds"], 1),
        warnings=warnings,
    )
