import threading
from pathlib import Path
from unittest import mock

from client.models import FileItem, FileStatus
from client.network.connection import load_runtime_config
from client.network.upload_queue import UploadQueue
from client.network.upload_worker import CANCELLED_STATUS, UploadCancelled, UploadWorker
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
