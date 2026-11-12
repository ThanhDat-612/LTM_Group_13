from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.part_manager import PartManager
from server.security import SecurityError, safe_upload_path


def test_part_manager_reserves_unique_name(tmp_path):
    manager = PartManager(tmp_path)

    first = manager.reserve_file("demo.txt")
    second = manager.reserve_file("demo.txt")

    assert first.exists()
    assert second.exists()
    assert first.name != second.name
    assert first.parent == tmp_path


def test_safe_upload_path_rejects_traversal(tmp_path):
    try:
        safe_upload_path(tmp_path, "../escape.txt")
    except SecurityError:
        return

    raise AssertionError("safe_upload_path should reject parent traversal")
