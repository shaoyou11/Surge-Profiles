import importlib.util
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory


MODULE_PATH = Path(__file__).parents[1] / "sync_rules.py"
SPEC = importlib.util.spec_from_file_location("sync_rules", MODULE_PATH)
sync_rules = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_rules)


class RuleHandler(BaseHTTPRequestHandler):
    responses = {}

    def do_GET(self):
        status, body = self.responses.get(self.path, (404, b"not found"))
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        pass


class SyncRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), RuleHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_valid_rule_replaces_existing_file(self):
        RuleHandler.responses["/valid.list"] = (200, b"DOMAIN-SUFFIX,example.com\n")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "Valid.list"
            target.write_text("old\n", encoding="utf-8")

            ok, _message = sync_rules.sync_source(
                root,
                {"path": "Valid.list", "url": f"{self.base_url}/valid.list"},
            )

            self.assertTrue(ok)
            self.assertEqual(target.read_text(encoding="utf-8"), "DOMAIN-SUFFIX,example.com\n")

    def test_html_error_page_preserves_last_good_file(self):
        RuleHandler.responses["/html.list"] = (200, b"<!doctype html><html>error</html>")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "HTML.list"
            target.write_text("last-good\n", encoding="utf-8")

            ok, _message = sync_rules.sync_source(
                root,
                {"path": "HTML.list", "url": f"{self.base_url}/html.list"},
            )

            self.assertFalse(ok)
            self.assertEqual(target.read_text(encoding="utf-8"), "last-good\n")

    def test_failed_download_preserves_last_good_file(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "Missing.list"
            target.write_text("last-good\n", encoding="utf-8")

            ok, _message = sync_rules.sync_source(
                root,
                {"path": "Missing.list", "url": f"{self.base_url}/missing.list"},
            )

            self.assertFalse(ok)
            self.assertEqual(target.read_text(encoding="utf-8"), "last-good\n")

    def test_duplicate_manifest_paths_are_rejected(self):
        with TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "sources.json"
            manifest.write_text(
                json.dumps(
                    [
                        {"path": "Same.list", "url": "https://example.com/one"},
                        {"path": "Same.list", "url": "https://example.com/two"},
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "duplicate path"):
                sync_rules.load_sources(manifest)


if __name__ == "__main__":
    unittest.main()
