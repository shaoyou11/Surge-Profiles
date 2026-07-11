import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "sync_assets.py"


class SyncAssetsTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(MODULE_PATH.exists(), "sync_assets.py is required")
        spec = importlib.util.spec_from_file_location("sync_assets", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_accepts_png_and_rejects_html(self):
        module = self.load_module()
        self.assertTrue(module.validate_content(b"\x89PNG\r\n\x1a\ncontent", "png"))
        self.assertFalse(module.validate_content(b"<!doctype html><html>error</html>", "png"))

    def test_accepts_mmdb_marker_and_rejects_arbitrary_data(self):
        module = self.load_module()
        self.assertTrue(module.validate_content(b"database\xab\xcd\xefMaxMind.com", "mmdb"))
        self.assertFalse(module.validate_content(b"not-a-database", "mmdb"))

    def test_rejects_unsafe_target_path(self):
        module = self.load_module()
        with self.assertRaisesRegex(ValueError, "unsafe path"):
            module.validate_source({"path": "../secret", "url": "https://example.com/a", "type": "png"})


if __name__ == "__main__":
    unittest.main()
