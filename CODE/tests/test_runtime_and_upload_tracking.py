import json
import socket
import threading
from pathlib import Path
from unittest import mock

import pytest

from common.protocol import pack_json, recv_exact, recv_json, send_chunk, send_json
from server.duplicate_policy import resolve_duplicate_name
from server.validator import validate_filename

from client.models import FileItem, FileStatus
from client.network.connection import load_runtime_config
from client.network.upload_queue import UploadQueue
from client.network.upload_worker import CANCELLED_STATUS, UploadCancelled, UploadWorker
from server.config_loader import ConfigError, load_config
from server.server import Server


def test_client_config_reads_shared_values():
    config = load_runtime_config(Path(__file__).resolve().parents[1] / 'config.json')
    assert 'max_concurrent_uploads' in config
    assert 'chunk_size' in config
    assert 'timeout_seconds' in config
    assert config['max_concurrent_uploads'] >= 1


def test_file_item_tracks_status_from_upload_update():
    item = FileItem.from_upload_update('C:/tmp/a.txt', 'completed', 100, '0 B/s', 'done')
    assert item.path == 'C:/tmp/a.txt'
    assert item.status == FileStatus.COMPLETED
    assert item.progress == 100


def test_worker_distinguishes_cancel_from_socket_error():
    cancel_status, cancel_msg = UploadWorker._classify_exception(UploadCancelled(), False)
    socket_status, socket_msg = UploadWorker._classify_exception(ConnectionResetError(), False)

    assert cancel_status == CANCELLED_STATUS
    assert 'hủy' in cancel_msg.lower()
    assert socket_status == 'error'
    assert 'kết nối' in socket_msg.lower() or 'connection' in socket_msg.lower()


def test_upload_queue_requeues_failed_network_file():
    queue = UploadQueue(max_concurrent=1)
    queue.enqueue('a.txt')
    batch = queue.next_batch()
    assert batch == ['a.txt']

    queue.requeue('a.txt')
    assert list(queue.queue) == ['a.txt']
    assert 'a.txt' not in queue.active


def test_config_loader_requires_values_from_config_file(tmp_path):
    cfg = tmp_path / 'config.json'
    cfg.write_text(json.dumps({
        'server_host': '127.0.0.1',
        'server_port': 5000,
    }), encoding='utf-8')

    try:
        load_config(cfg)
        raise AssertionError('Expected ConfigError for missing required keys')
    except ConfigError as exc:
        assert 'Thiếu trường bắt buộc' in str(exc)


def test_manager_does_not_keep_stale_cancel_for_readded_file():
    manager = __import__('client.network.upload_manager', fromlist=['UploadManager']).UploadManager(
        '127.0.0.1', 1234, lambda *args, **kwargs: None, max_concurrent=1
    )
    file_path = 'a.txt'
    manager._cancel_requested.add(file_path)

    with mock.patch('client.network.upload_manager.UploadWorker') as mock_worker:
        manager.add_files([file_path])

        assert file_path not in manager._cancel_requested
        assert not mock_worker.return_value.stop.called


def test_server_limiter_applies_to_client_sessions_not_every_upload_socket():
    server = Server.__new__(Server)
    server.is_running = True
    fake_socket = mock.Mock()
    server.server_socket = fake_socket
    server.connections = {}
    server.connected_clients = {}
    server._active_handlers = 0
    server.lock = threading.RLock()
    server.log = lambda *args, **kwargs: None
    server.connection_limiter = mock.Mock()

    accepted = {"done": False}

    def fake_accept():
        if not accepted["done"]:
            accepted["done"] = True
            server.is_running = False
            return mock.Mock(), ("127.0.0.1", 5000)
        raise OSError("stop")

    fake_socket.accept.side_effect = fake_accept
    fake_socket.close = mock.Mock()

    with mock.patch("threading.Thread.start", lambda *args, **kwargs: None):
        server._accept_loop(server.server_socket)

    server.connection_limiter.acquire.assert_not_called()


@pytest.mark.parametrize("name", [
    "",
    ".",
    "..",
    "folder/file.txt",
    "folder\\file.txt",
    " file.txt",
    "file.txt ",
    ".hidden.txt",
    "file.txt.part",
    "bad<name.txt",
    "CON.txt",
])
def test_validate_filename_rejects_invalid_names(name):
    with pytest.raises(ValueError):
        validate_filename(name)


def test_validate_filename_accepts_regular_name():
    assert validate_filename("baocao-2026.txt") == "baocao-2026.txt"


def test_duplicate_name_keeps_original_when_available(tmp_path):
    assert resolve_duplicate_name("report.txt", tmp_path) == "report.txt"


def test_duplicate_name_creates_timestamped_name(tmp_path):
    (tmp_path / "report.txt").write_bytes(b"existing")

    fixed_now = mock.Mock()
    fixed_now.strftime.return_value = "28112026_120000"
    with mock.patch("server.duplicate_policy.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        name = resolve_duplicate_name("report.txt", tmp_path)

    assert name == "report_28112026_120000.txt"


def test_protocol_json_and_raw_chunk_roundtrip():
    left, right = socket.socketpair()
    try:
        payload = {"type": "UPLOAD_ACK", "status": "ok", "name": "báo cáo.txt"}
        send_json(left, payload)
        assert recv_json(right) == payload

        send_chunk(left, b"abc123")
        length = recv_exact(right, 4)
        assert int.from_bytes(length, "big") == 6
        assert recv_exact(right, 6) == b"abc123"
    finally:
        left.close()
        right.close()


def test_upload_queue_limits_concurrency_and_removes_pending():
    queue = UploadQueue(max_concurrent=2)
    queue.enqueue("a.txt")
    queue.enqueue("b.txt")
    queue.enqueue("c.txt")

    assert queue.next_batch() == ["a.txt", "b.txt"]
    assert queue.next_batch() == []
    assert queue.remove("c.txt") is True
    assert queue.clear_pending() == []

    queue.mark_done("a.txt")
    assert "a.txt" not in queue.active
