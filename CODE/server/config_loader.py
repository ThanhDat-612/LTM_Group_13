"""Đọc và kiểm tra config.json. Thiếu khoá thì dùng giá trị mặc định; sai giá trị thì báo lỗi rõ ràng."""
import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULTS = {
    "server_host": "127.0.0.1",
    "server_port": 5000,
    "upload_dir": "server/storage/uploads",
    "log_dir": "server/logs",
    "stop_password": "admin123",
    "max_file_size_mb": 4096,   # 0 = không giới hạn
    "max_log_files": 30,        # số tệp log giữ lại, 0 = giữ tất cả
}
# Các khoá có thể nằm chung trong config.json nhưng do phía client hoặc phần khác đọc,
# server không dùng nên bỏ qua, không cảnh báo.
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
    raw = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"{path.name} không phải JSON hợp lệ: {exc.msg} (dòng {exc.lineno}, cột {exc.colno})")
        except OSError as exc:
            raise ConfigError(f"Không đọc được {path}: {exc}")
        if not isinstance(raw, dict):
            raise ConfigError(f"{path.name} phải là một đối tượng JSON {{...}}")

    data = dict(DEFAULTS)
    warnings = []
    for key, value in raw.items():
        key = ALIASES.get(key, key)
        if key in DEFAULTS:
            data[key] = value
        elif key in SHARED_KEYS:
            continue
        else:
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
        warnings=warnings,
    )