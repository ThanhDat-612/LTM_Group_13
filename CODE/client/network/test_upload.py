from client.network.upload_manager import UploadManager
from client.network.upload_worker import UploadWorker


def make_worker():
    return UploadWorker(
        host="127.0.0.1",
        port=5000,
        chunk_size=1024 * 1024,
        progress_callback=lambda s: print(
            f"{s.file_id}: "
            f"{s.percent:.1f}% | "
            f"{s.bytes_per_second / 1024:.1f} KB/s"
        ),
    )


manager = UploadManager(
    worker_factory=make_worker,
    max_concurrent=2,
)

manager.add_file(r"C:\Users\ADMIN\Downloads\big_test.bin")

results = manager.run()

for result in results:
    print(result)
