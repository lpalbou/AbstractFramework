"""install.sh --with-wheel: local framework wheels replace their release pins.

Found on the Linux test server (2026-10-29): fix wheels of abstractcore / AbstractRuntime were
side-loaded with `uv pip install` into the gateway's tool while `uv-constraints.txt` and the uv
tool receipt still pinned abstractcore==2.31.0 / AbstractRuntime==0.15.0, so any later
`uv tool upgrade` or installer re-run put the old versions back. `--with-wheel PATH` installs the
wheel through `uv tool install --with` and drops its package from the constraints, so the receipt
and uv-constraints.txt record what is really installed. Driven with --print (nothing is
installed) in a throwaway HOME.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SH = ROOT / "scripts" / "install.sh"
TEXT = SH.read_text(encoding="utf-8")
MATRIX = dict(c.split("==", 1) for c in re.search(r'^AF_PY_MATRIX="([^"]+)"', TEXT, re.M).group(1).split())

pytestmark = pytest.mark.skipif(sys.platform.startswith("win"), reason="install.sh is the POSIX installer")


def _wheel(tmp: Path, name: str) -> Path:
    path = tmp / "wheels dir" / f"{name}-9.9.9-py3-none-any.whl"  # a space: paths must survive
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return path


def _plan(tmp: Path, *args: str) -> subprocess.CompletedProcess:
    home = tmp / "home"
    home.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("AF_")}
    env["HOME"] = str(home)
    return subprocess.run(["sh", str(SH), "--print", "--yes", "--profile", "light", "--port", "18831", *args],
                          capture_output=True, text=True, env=env, timeout=300)


def _constraints_block(out: str) -> list[str]:
    lines = out.splitlines()
    start = next(i for i, l in enumerate(lines) if "uv-constraints.txt" in l)
    block = []
    for l in lines[start + 1:]:
        if not l.startswith("      "):
            break
        block.append(l.strip())
    return block


def test_a_wheel_replaces_its_release_pin(tmp_path):
    core = _wheel(tmp_path, "abstractcore")
    runtime = _wheel(tmp_path, "abstractruntime")
    res = _plan(tmp_path, "--with-wheel", str(core), f"--with-wheel={runtime}")
    assert res.returncode == 0, res.stdout + res.stderr
    pins = _constraints_block(res.stdout)
    assert f"abstractagent=={MATRIX['abstractagent']}" in pins
    assert not any(p.lower().startswith(("abstractcore==", "abstractruntime==")) for p in pins), (
        f"MUTANT: the wheel's package kept its release pin -> uv-constraints.txt rolls it back: {pins}")
    cmd = next(l for l in res.stdout.splitlines() if "tool install" in l)
    assert str(core) in cmd and str(runtime) in cmd, cmd


def test_without_wheels_the_release_matrix_is_whole(tmp_path):
    res = _plan(tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr
    assert f"abstractcore=={MATRIX['abstractcore']}" in _constraints_block(res.stdout)


@pytest.mark.parametrize("name,why", [
    ("abstractgateway", "--from"),
    ("abstractvoice", "voice extras"),
    ("numpy", "not a package of the AbstractFramework release matrix"),
])
def test_wheels_it_cannot_take_are_refused(tmp_path, name, why):
    res = _plan(tmp_path, "--with-wheel", str(_wheel(tmp_path, name)))
    assert res.returncode == 2 and why in res.stderr, res.stdout + res.stderr


def test_a_missing_wheel_is_refused(tmp_path):
    res = _plan(tmp_path, "--with-wheel", str(tmp_path / "abstractcore-1-py3-none-any.whl"))
    assert res.returncode == 2 and "no such file" in res.stderr


def test_a_relative_wheel_path_is_made_absolute(tmp_path):
    """Review: the install runs from the data dir; a relative path must survive."""
    core = _wheel(tmp_path, "abstractcore")
    env_cwd = core.parent
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("AF_")}
    env["HOME"] = str(home)
    res = subprocess.run(["sh", str(SH), "--print", "--yes", "--profile", "light", "--port", "18831",
                          "--with-wheel", f"./{core.name}"], capture_output=True, text=True, env=env, cwd=env_cwd, timeout=300)
    assert res.returncode == 0, res.stdout + res.stderr
    cmd = next(l for l in res.stdout.splitlines() if "tool install" in l)
    assert str(core) in cmd, cmd
