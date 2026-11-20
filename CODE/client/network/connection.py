import json
import socket
from pathlib import Path

DEFAULT_RUNTIME_CONFIG = {
    "server_host": "127.0.0.1",
    "server_port": 5000,
    "max_concurrent_uploads": 3,
    "chunk_size": 65536,
    "timeout_seconds": 30,
    "upload_dir": "server/storage/uploads",
    "log_dir": "server/logs",
}


def _candidate_config_paths(config_path=None):
    candidates = []
    if config_path is not None:
        custom = Path(config_path).expanduser()
        if custom.is_absolute():
            candidates.append(custom)
        else:
            candidates.extend([
                Path.cwd() / custom,
                Path(__file__).resolve().parents[2] / custom,
            ])
    candidates.extend([
        Path(__file__).resolve().parents[2] / "config.json",
        Path.cwd() / "config.json",
    ])

    seen = set()
    ordered = []
    for candidate in candidates:
        normalized = str(candidate.resolve())
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(candidate)
    return ordered


def load_runtime_config(config_path="config.json"):
    """Load the shared runtime config used by both client and server."""
    config = dict(DEFAULT_RUNTIME_CONFIG)
    for candidate in _candidate_config_paths(config_path):
        if not candidate.exists():
            continue
        try:
            with candidate.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict):
            continue
        for key, default_value in DEFAULT_RUNTIME_CONFIG.items():
            if key in raw:
                value = raw[key]
                if isinstance(default_value, int):
                    try:
                        config[key] = int(value)
                    except (TypeError, ValueError):
                        config[key] = default_value
                else:
                    config[key] = value
        break
    return config


def check_connection(host, port, timeout=None):
    """Kiểm tra kết nối TCP đến server."""
    runtime = load_runtime_config()
    timeout = runtime.get("timeout_seconds", 30) if timeout is None else timeout
    try:
        port = int(port)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
    return False


def ping_server(host, port, timeout=2):
    runtime = load_runtime_config()
    effective_timeout = runtime.get("timeout_seconds", timeout)
    try:
        port = int(port)
        start = __import__("time").time()
        with socket.create_connection((host, port), timeout=effective_timeout):
            elapsed_ms = (__import__("time").time() - start) * 1000
            return round(elapsed_ms, 1)
    except OSError:
        return None


