#!/usr/bin/env python3
"""Local, token-protected bridge from Sandbox Reply Lab to upstream REA on Termux."""
import argparse
import hmac
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import zipfile

MAX_UPLOAD = 128 * 1024 * 1024
MAX_RESULT = 192 * 1024


def inspect_archive(raw: bytes, mode: str, kind: str, root: Path) -> dict:
    if mode not in ("inventory", "deep") or kind not in ("apk", "xapk"):
        raise ValueError("Invalid mode or package type")
    if not (4 <= len(raw) <= MAX_UPLOAD) or raw[:2] != b"PK":
        raise ValueError("Invalid ZIP/APK archive or size limit exceeded")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zin:
            if zin.testzip() is not None:
                raise ValueError("Corrupt archive")
            if kind == "xapk" and mode == "deep":
                entries = [p for p in zin.infolist()
                           if not p.is_dir() and p.filename.lower().endswith(".apk")]
                if not entries:
                    raise ValueError("XAPK contains no APK")
                entries.sort(key=lambda p: (p.filename.lower().split("/")[-1] != "base.apk",
                                            p.filename.lower()))
                entry = entries[0]
                if entry.file_size > MAX_UPLOAD:
                    raise ValueError("Nested APK exceeds size limit")
                with zin.open(entry) as f:
                    raw = f.read(MAX_UPLOAD + 1)
                if len(raw) > MAX_UPLOAD or raw[:2] != b"PK":
                    raise ValueError("Invalid nested APK")
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise ValueError("Invalid ZIP structure") from exc

    cli = root / "scripts" / "rea.mjs"
    compiled = root / "dist" / "cli-runtime" / "cli.js"
    if not cli.is_file() or not compiled.is_file():
        raise RuntimeError("REA is not built in Termux")
    if shutil.which("node") is None:
        raise RuntimeError("Missing Node.js")
    with tempfile.TemporaryDirectory(prefix="srl-rea-") as tmp:
        suffix = ".xapk" if kind == "xapk" and mode == "inventory" else ".apk"
        archive = Path(tmp) / ("scan" + suffix)
        archive.write_bytes(raw)
        cmd = ["node", str(cli),
               "inspect-artifact" if mode == "inventory" else "inspect-android-package",
               str(archive), "--json"]
        try:
            result = subprocess.run(cmd, cwd=root, capture_output=True,
                                    timeout=120, check=False)
        except subprocess.TimeoutExpired:
            return {"ok": False, "engine": "REA 6.4.0 / Termux",
                    "error": "REA timed out after 120 seconds"}
    return {
        "ok": result.returncode == 0,
        "engine": "REA upstream / Termux",
        "mode": mode,
        "exit_code": result.returncode,
        "output": result.stdout[:MAX_RESULT].decode("utf-8", errors="replace"),
        "stderr": result.stderr[:12000].decode("utf-8", errors="replace"),
        "truncated": len(result.stdout) > MAX_RESULT,
        "note": "Deep APK analysis requires a compatible JADX/JVM setup.",
    }


class Handler(BaseHTTPRequestHandler):
    token = ""
    rea_root = Path(".")

    def log_message(self, fmt, *args):
        pass

    def answer(self, status: int, payload: dict):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        return hmac.compare_digest(self.headers.get("X-Sandbox-Token", ""), self.token)

    def do_GET(self):
        if self.path != "/health":
            return self.answer(404, {"error": "Not found"})
        if not self.authorized():
            return self.answer(403, {"error": "Unauthorized"})
        built = (self.rea_root / "dist/cli-runtime/cli.js").is_file()
        return self.answer(200, {"ok": built, "built": built, "engine": "rea-upstream-termux"})

    def do_POST(self):
        if self.path != "/analyze":
            return self.answer(404, {"error": "Not found"})
        if not self.authorized():
            return self.answer(403, {"error": "Unauthorized"})
        try:
            size = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            size = -1
        if not (0 < size <= MAX_UPLOAD):
            return self.answer(413, {"error": "Upload size invalid or exceeds limit"})
        raw = bytearray()
        while len(raw) < size:
            part = self.rfile.read(min(65536, size-len(raw)))
            if not part:
                return self.answer(400, {"error": "Incomplete upload"})
            raw.extend(part)
        try:
            result = inspect_archive(bytes(raw),
                                     self.headers.get("X-Rea-Mode", "inventory"),
                                     self.headers.get("X-Package-Type", "apk"),
                                     self.rea_root)
        except (OSError, ValueError, RuntimeError) as exc:
            return self.answer(400, {"ok": False, "error": str(exc)})
        return self.answer(200 if result["ok"] else 422, result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rea-dir", required=True)
    parser.add_argument("--port", type=int, default=18767)
    args = parser.parse_args()
    root = Path(args.rea_dir).expanduser().resolve()
    if not (root / "scripts/rea.mjs").is_file():
        raise SystemExit("REA source was not found: " + str(root))
    Handler.rea_root = root
    Handler.token = secrets.token_urlsafe(32)
    print("REA local bridge: 127.0.0.1:" + str(args.port))
    print("TOKEN: " + Handler.token, flush=True)
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
