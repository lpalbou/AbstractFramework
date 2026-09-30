"""install.sh on Linux + NVIDIA (gpu profile): "The same steps by hand" include llama.cpp's CUDA
build swap (0.7.0 Linux end-to-end F4: the printed steps named only the cpu wheel's install line,
so following them by hand gave a CPU-only llama.cpp).

Simulated on any POSIX host with stub `uname`, `nvidia-smi` and `ldd` (nothing is installed:
`--print`)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("sh") is None, reason="needs a POSIX sh")
def test_print_twin_swaps_in_llama_cpp_cuda_build(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stubs = {
        "uname": 'case "$1" in -s) echo Linux;; -m) echo x86_64;; *) echo Linux;; esac',
        "nvidia-smi": 'echo "Quadro RTX 5000, 580.65, 16384, 7.5"',
        "ldd": 'echo "ldd (Ubuntu GLIBC 2.39) 2.39"',
    }
    for name, body in stubs.items():
        path = bin_dir / name
        path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        path.chmod(0o755)
    home = tmp_path / "home"
    home.mkdir()
    env = {"PATH": f"{bin_dir}{os.pathsep}/usr/bin{os.pathsep}/bin{os.pathsep}/usr/sbin", "HOME": str(home)}
    out = subprocess.run(
        ["sh", str(ROOT / "scripts" / "install.sh"), "--print", "--profile", "gpu", "--port", "18829"],
        capture_output=True, text=True, env=env, timeout=120,
    ).stdout
    assert "The same steps by hand:" in out, out[-2000:]
    twins = out.split("The same steps by hand:", 1)[1]
    install = next(line for line in twins.splitlines() if "uv tool install" in line)
    assert "/whl/cpu/llama-cpp-python/" in install  # the install itself takes the cpu wheel
    swap = [line for line in twins.splitlines() if "uv pip install" in line and "/whl/cu130/llama-cpp-python/" in line]
    assert swap and "--reinstall-package llama-cpp-python" in swap[0] and "cu125" in swap[0]
