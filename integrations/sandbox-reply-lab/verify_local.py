#!/usr/bin/env python3
"""Small checks requiring no REA installation or external network."""
import io
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rea_local_server as bridge


def zip_bytes(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return out.getvalue()


class BridgeChecks(unittest.TestCase):
    def test_rejects_unknown_mode(self):
        with self.assertRaisesRegex(ValueError, "mode"):
            bridge.inspect_archive(zip_bytes({"a": b"a"}), "unknown", "apk", Path("."))

    def test_rejects_invalid_archive(self):
        with self.assertRaises(ValueError):
            bridge.inspect_archive(b"not-an-apk", "inventory", "apk", Path("."))

    def test_rejects_xapk_without_apk(self):
        with self.assertRaisesRegex(ValueError, "no APK"):
            bridge.inspect_archive(zip_bytes({"manifest.json": b"{}"}), "deep", "xapk", Path("."))

    def test_requires_built_rea(self):
        with TemporaryDirectory() as d:
            with self.assertRaisesRegex(RuntimeError, "not built"):
                bridge.inspect_archive(zip_bytes({"classes.dex": b"demo"}), "inventory", "apk", Path(d))

    def test_token_must_match(self):
        class FakeRequest:
            token = "correct-test-token"
            headers = {"X-Sandbox-Token": "wrong"}
        self.assertFalse(bridge.Handler.authorized(FakeRequest()))
        FakeRequest.headers = {"X-Sandbox-Token": "correct-test-token"}
        self.assertTrue(bridge.Handler.authorized(FakeRequest()))


if __name__ == "__main__":
    unittest.main()
