"""install.sh on macOS older than 14 picks the light profile; a re-run after the macOS update adds
the Apple Silicon engines (root backlog 1002, round 14).

MLX publishes no wheels below macOS 14 (`macosx_14_0_arm64` is its oldest tag, no source package),
so `abstractframework[apple]` does not resolve on macOS 13. The installer's auto profile picks light
there and refuses `--profile apple`. It records in its state file (PROFILE_WHY=macos) that light was
picked only because of the macOS version, so the re-run its message asks for, after a macOS update,
switches to apple; an explicit `--profile light` (no PROFILE_WHY) stays light.

`sw_vers` and `uname -m` are stubbed; `install.sh --print` changes nothing. The installer's OS check
reads the real `uname -s`, so these run on macOS only.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SH = ROOT / "scripts" / "install.sh"

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="install.sh reads the real uname -s")


def _run(tmp_path: Path, macos: str, *extra: str, state: str | None = None) -> subprocess.CompletedProcess[str]:
    fake = tmp_path / "fakebin"
    fake.mkdir(exist_ok=True)
    real_uname = shutil.which("uname")
    stubs = {
        "sw_vers": f'#!/bin/sh\n[ "$1" = -productVersion ] && echo {macos} && exit 0\nexit 1\n',
        "uname": f'#!/bin/sh\ncase "$1" in -m) echo arm64 ;; *) {real_uname} "$@" ;; esac\n',
        "xcode-select": "#!/bin/sh\nexit 0\n",
    }
    for name, body in stubs.items():
        (fake / name).write_text(body)
        (fake / name).chmod(0o755)
    data = tmp_path / "data"
    data.mkdir(exist_ok=True)
    if state is not None:
        (data / "bootstrap.env").write_text(state)
    return subprocess.run(
        ["sh", str(SH), "--print", "--port", "18999", "--no-tray", *extra],
        capture_output=True,
        text=True,
        timeout=120,
        env={"HOME": str(tmp_path), "AF_DATA_DIR": str(data), "PATH": f"{fake}:/usr/bin:/bin:/usr/sbin:/sbin", "TERM": "dumb"},
    )


def _profile(out: str) -> str:
    m = re.search(r"profile: (\w+) \(", out)
    assert m, out[-2000:]
    return m.group(1)


def _install_line(out: str) -> str:
    return next(line for line in out.splitlines() if " tool install --python 3.12 " in line)


def test_macos_13_picks_light(tmp_path):
    res = _run(tmp_path, "13.6.1")
    assert res.returncode == 0, res.stdout[-2000:] + res.stderr
    assert _profile(res.stdout) == "light"
    assert "the Apple Silicon engines (MLX) need macOS 14 or later" in res.stdout
    assert "abstractgateway[apple" not in _install_line(res.stdout)


def test_macos_13_refuses_profile_apple(tmp_path):
    res = _run(tmp_path, "13.6.1", "--profile", "apple")
    assert res.returncode != 0
    assert "the apple profile needs macOS 14 or later (this is 13.6.1)" in res.stdout + res.stderr


def test_macos_14_picks_apple(tmp_path):
    res = _run(tmp_path, "14.5")
    assert res.returncode == 0, res.stdout[-2000:] + res.stderr
    assert _profile(res.stdout) == "apple"
    assert "abstractgateway[apple" in _install_line(res.stdout)


def test_rerun_after_macos_update_adds_apple(tmp_path):
    res = _run(tmp_path, "14.5", state="PORT=18999\nPROFILE=light\nPROFILE_WHY=macos\n")
    assert res.returncode == 0, res.stdout[-2000:] + res.stderr
    assert _profile(res.stdout) == "apple"
    assert "the previous install was light only because macOS was older than 14" in res.stdout


def test_rerun_still_on_macos_13_stays_light(tmp_path):
    res = _run(tmp_path, "13.7", state="PORT=18999\nPROFILE=light\nPROFILE_WHY=macos\n")
    assert res.returncode == 0, res.stdout[-2000:] + res.stderr
    assert _profile(res.stdout) == "light"
    assert "need macOS 14 or later" in res.stdout


def test_explicit_light_is_kept_after_macos_update(tmp_path):
    res = _run(tmp_path, "14.5", state="PORT=18999\nPROFILE=light\nPROFILE_WHY=\n")
    assert res.returncode == 0, res.stdout[-2000:] + res.stderr
    assert _profile(res.stdout) == "light"
    assert "kept from the previous install" in res.stdout


def test_state_file_records_why():
    text = SH.read_text(encoding="utf-8")
    assert 'echo "PROFILE_WHY=$PROFILE_WHY"' in text
    # --print writes no state: the two auto branches that pick light for the macOS version
    # (fresh, and a re-run still below 14) must both record it.
    assert text.count("PROFILE=light; PROFILE_WHY=macos") == 2
