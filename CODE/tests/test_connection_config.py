import json
import tempfile
import unittest
from pathlib import Path

from server.server import Server


class ServerConfigTest(unittest.TestCase):
    def test_server_reads_project_config_keys(self):
        cfg = {
            "server_host": "127.0.0.1",
            "server_port": 5000,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            path.write_text(json.dumps(cfg), encoding="utf-8")

            server = Server(config_path=str(path))
            try:
                self.assertEqual(server.host, "127.0.0.1")
                self.assertEqual(server.port, 5000)
            finally:
                server.stop()


if __name__ == "__main__":
    unittest.main()
