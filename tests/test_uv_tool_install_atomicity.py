"""A failed `uv tool install` leaves the previous tool environment in place and working.

The installers retry a network failure and then stop with "nothing was changed: uv changes the
gateway's environment only after every download succeeded" (install.sh, above AF_UV_DETERMINISTIC).
This proves that sentence with the real uv on this machine: a tool is installed from a local index,
then upgraded while the index answers 502, 429 or resets the connection for the new wheel, in the
ways the installer runs uv (a new version, an added --with, --reinstall, another Python). After each
failure the old command still runs and still reports the old version.

Real uv, no network: the index is a local HTTP server, every uv directory is under tmp_path, uv's own
config and Python downloads are off. Skipped without uv.
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import os
import shutil
import socket
import struct
import subprocess
import sys
import threading
import zipfile
from pathlib import Path

import pytest

UV = shutil.which("uv")
pytestmark = pytest.mark.skipif(UV is None, reason="needs uv")


def _wheel(out: Path, name: str, version: str) -> None:
    dist = f"{name}-{version}.dist-info"
    files = {
        f"{name}/__init__.py": f"def main():\n    print('{name} {version}')\n",
        f"{dist}/METADATA": f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n",
        f"{dist}/WHEEL": "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        f"{dist}/entry_points.txt": f"[console_scripts]\n{name} = {name}:main\n",
    }
    record = []
    with zipfile.ZipFile(out / f"{name}-{version}-py3-none-any.whl", "w") as z:
        for path, text in files.items():
            z.writestr(path, text)
            digest = base64.urlsafe_b64encode(hashlib.sha256(text.encode()).digest()).rstrip(b"=").decode()
            record.append(f"{path},sha256={digest},{len(text)}")
        record.append(f"{dist}/RECORD,,")
        z.writestr(f"{dist}/RECORD", "\n".join(record) + "\n")


class _Index(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, files: Path) -> None:
        self.files = files
        self.fail: set[str] = set()
        self.mode = "502"
        super().__init__(("127.0.0.1", 0), _Handler)


class _Handler(http.server.BaseHTTPRequestHandler):
    server: _Index

    def do_GET(self) -> None:  # noqa: N802
        parts = [p for p in self.path.split("/") if p]
        if parts[:1] == ["simple"] and len(parts) == 2:
            links = "".join(f'<a href="/files/{f.name}">{f.name}</a>\n' for f in sorted(self.server.files.iterdir())
                            if f.name.startswith(parts[1] + "-"))
            return self._send(200, f"<html><body>{links}</body></html>".encode(), "text/html") if links else self._send(404, b"")
        if parts[:1] == ["files"] and len(parts) == 2:
            if parts[1] in self.server.fail:
                if self.server.mode == "reset":
                    self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
                    self.connection.close()
                    return None
                return self._send(int(self.server.mode), b"error")
            return self._send(200, (self.server.files / parts[1]).read_bytes())
        return self._send(404, b"")

    do_HEAD = do_GET

    def _send(self, code: int, body: bytes, ctype: str = "application/octet-stream") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command == "GET":
            self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture()
def index(tmp_path: Path):
    files = tmp_path / "files"
    files.mkdir()
    for name, version in [("aftoolx", "1.0"), ("aftoolx", "2.0"), ("aftooly", "1.0")]:
        _wheel(files, name, version)
    srv = _Index(files)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()


def _uv(tmp_path: Path, index: _Index, *args: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("UV_", "PIP_")) and not k.upper().endswith(("_KEY", "_TOKEN", "PASSWORD"))}
    env.update({"HOME": str(tmp_path / "home"), "XDG_DATA_HOME": str(tmp_path / "xdg"), "UV_TOOL_DIR": str(tmp_path / "tools"),
                "UV_TOOL_BIN_DIR": str(tmp_path / "bin"), "UV_CACHE_DIR": str(tmp_path / "cache"), "UV_NO_CONFIG": "1",
                "UV_PYTHON_DOWNLOADS": "never", "UV_HTTP_RETRIES": "0", "NO_COLOR": "1"})
    return subprocess.run([UV, "tool", "install", "--index-url", f"http://127.0.0.1:{index.server_address[1]}/simple", *args],
                          capture_output=True, text=True, env=env, timeout=120)


def _runs(tmp_path: Path) -> str:
    return subprocess.run([str(tmp_path / "bin" / "aftoolx")], capture_output=True, text=True, timeout=30).stdout.strip()


@pytest.mark.parametrize("mode", ["502", "429", "reset"])
@pytest.mark.parametrize("change", ["new-version", "added-with", "reinstall"])
def test_a_failed_tool_upgrade_leaves_the_previous_tool_working(tmp_path: Path, index: _Index, mode: str, change: str) -> None:
    py = sys.executable
    first = _uv(tmp_path, index, "--python", py, "aftoolx==1.0")
    assert first.returncode == 0, first.stderr
    assert _runs(tmp_path) == "aftoolx 1.0"
    index.fail = {"aftoolx-2.0-py3-none-any.whl", "aftooly-1.0-py3-none-any.whl"}
    index.mode = mode
    shutil.rmtree(tmp_path / "cache")  # the new wheels must come from the (failing) index
    args = {"new-version": ["aftoolx==2.0"], "added-with": ["--with", "aftooly==1.0", "aftoolx==1.0"],
            "reinstall": ["--reinstall", "aftoolx==2.0"]}[change]
    failed = _uv(tmp_path, index, "--python", py, *args)
    assert failed.returncode != 0, failed.stdout + failed.stderr
    # The installer's classifier calls these failures transient (the strings it matches).
    text = " ".join((failed.stdout + failed.stderr).split()).lower()
    assert ("http status server error (502" in text) or ("http status client error (429" in text) or ("connection reset" in text), text
    assert _runs(tmp_path) == "aftoolx 1.0"
    receipt = (tmp_path / "tools" / "aftoolx" / "uv-receipt.toml").read_text()
    assert "aftooly" not in receipt and "==1.0" in receipt, receipt


def test_a_failed_upgrade_to_another_python_leaves_the_previous_tool_working(tmp_path: Path, index: _Index) -> None:
    """uv says "Ignoring existing environment ... interpreter does not match" and builds a new one:
    the old one must survive a failed download too. Needs a second local Python (no downloads)."""
    env = {**os.environ, "UV_PYTHON_DOWNLOADS": "never", "UV_NO_CONFIG": "1"}
    pythons = []
    for v in ("3.13", "3.12", "3.11", "3.10"):
        r = subprocess.run([UV, "python", "find", v], capture_output=True, text=True, env=env)
        if r.returncode == 0 and r.stdout.strip() and r.stdout.strip() not in pythons:
            pythons.append(r.stdout.strip())
    if len(pythons) < 2:
        pytest.skip("needs two local Pythons")
    assert _uv(tmp_path, index, "--python", pythons[1], "aftoolx==1.0").returncode == 0
    index.fail = {"aftoolx-2.0-py3-none-any.whl"}
    shutil.rmtree(tmp_path / "cache")
    failed = _uv(tmp_path, index, "--python", pythons[0], "aftoolx==2.0")
    assert failed.returncode != 0
    assert _runs(tmp_path) == "aftoolx 1.0"
