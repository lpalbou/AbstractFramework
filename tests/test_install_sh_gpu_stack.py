"""install.sh, the gpu setting on Linux + NVIDIA (root backlog 0989).

Measured on a Linux + NVIDIA test machine (Quadro RTX 5000, driver 595): the gpu install got
llama.cpp's CPU wheel only, and its 14 GB resolve printed nothing for its whole duration. install.sh
now reads the driver and compute capability from nvidia-smi, swaps in llama.cpp's CUDA build that
matches PyTorch's CUDA (kept only when it loads and offloads), and shows uv's progress with a
heartbeat.

No NVIDIA hardware is needed: the installer's functions are cut out of the script (running the
script would install) and driven with a fake `nvidia-smi` on PATH. What is not covered here (needs
real hardware, done on the test machine): that the CUDA wheel really loads and offloads.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install.sh"


def _function(name: str) -> str:
    text = SCRIPT.read_text()
    one_line = re.search(rf"(?m)^{re.escape(name)}\(\) \{{.*\}}$", text)
    if one_line:
        return one_line.group(0)
    start = re.search(rf"(?m)^{re.escape(name)}\(\) \{{$", text)
    assert start, f"{name} not found in install.sh"
    end = text.index("\n}\n", start.end())
    return text[start.start(): end + 3]


def _assignments(*names: str) -> str:
    text = SCRIPT.read_text()
    out = []
    for n in names:
        m = re.search(rf'(?m)^{n}="[^"\n]*"$', text)
        assert m, n
        out.append(m.group(0))
    return "\n".join(out)


def _exe(path: Path, text: str) -> Path:
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def _sh(body: str, tmp_path: Path, *, smi: str | None = None) -> str:
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    if smi is not None:
        _exe(bindir / "nvidia-smi", smi)
    env = {"PATH": f"{bindir}:/usr/bin:/bin", "HOME": str(tmp_path), "LC_ALL": "C"}
    prelude = "\n".join(
        [
            "set -eu",
            'C_D=""; C_0=""',
            _function("have"),
            _assignments("AF_LLAMA_CUDA13", "AF_LLAMA_CUDA12"),
            _function("nvidia_info"),
            _function("llama_cuda_build"),
            _function("live_exec"),
        ]
    )
    shell = shutil.which("dash") or "/bin/sh"
    proc = subprocess.run([shell, "-c", prelude + "\n" + body], capture_output=True, text=True, env=env, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout


def _smi(answer: str, *, old_driver: bool = False) -> str:
    # A fake nvidia-smi: answers the compute_cap query unless it plays an old driver.
    return (
        "#!/bin/sh\n"
        'case "$*" in\n'
        f"  *compute_cap*) {'exit 6' if old_driver else 'cat <<EOF'}\n"
        + ("" if old_driver else f"{answer}\nEOF\n")
        + "  ;;\n"
        "  *) cat <<EOF\n"
        + "\n".join(line.split(",")[0] + "," + line.split(",")[-1] for line in answer.splitlines())
        + "\nEOF\n  ;;\nesac\n"
    )


REPORT = 'nvidia_info; echo "ok=$NV_OK driver=$NV_DRIVER major=$NV_MAJOR cc=$NV_CC10 name=$NV_NAME err=$NV_ERR"'


def test_the_test_machine_answer_is_read(tmp_path):
    out = _sh(REPORT, tmp_path, smi=_smi("595.91.07, 7.5, Quadro RTX 5000"))
    assert out.strip() == "ok=1 driver=595.91.07 major=595 cc=75 name=Quadro RTX 5000 err="


def test_several_gpus_take_the_lowest_compute_capability(tmp_path):
    out = _sh(REPORT, tmp_path, smi=_smi("581.10, 8.9, NVIDIA L4\n581.10, 7.0, Tesla V100"))
    assert "cc=70" in out and "name=NVIDIA L4" in out


def test_a_driver_too_old_for_compute_cap_is_judged_by_its_version(tmp_path):
    out = _sh(REPORT, tmp_path, smi=_smi("516.94, 8.6, RTX 3060", old_driver=True))
    assert "ok=1 driver=516.94 major=516 cc= name=RTX 3060" in out


def test_no_or_failing_nvidia_smi_means_no_gpu(tmp_path):
    assert "ok=0" in _sh(REPORT, tmp_path) and "nvidia-smi not found" in _sh(REPORT, tmp_path)
    out = _sh(REPORT, tmp_path, smi="#!/bin/sh\necho 'NVIDIA-SMI has failed' >&2\nexit 9\n")
    assert "ok=0" in out and "no answer" in out


@pytest.mark.parametrize(
    "answer, torch_cuda, expected",
    [
        ("595.91.07, 7.5, Quadro RTX 5000", "13", "cu130"),
        ("595.91.07, 7.5, Quadro RTX 5000", "12", "cu125"),
        ("560.35, 8.6, RTX 3090", "12", "cu125"),
        ("560.35, 8.6, RTX 3090", "13", ""),  # CUDA 13 torch needs driver 580+
        ("516.94, 8.6, RTX 3060", "12", ""),  # CUDA 12 needs 525+
        ("595.91.07, 7.5, Quadro RTX 5000", "", ""),  # CPU torch
    ],
)
def test_llama_build_follows_torch_cuda_and_the_driver(tmp_path, answer, torch_cuda, expected):
    out = _sh(f'nvidia_info; b="$(llama_cuda_build "{torch_cuda}")"; echo "build=$b"', tmp_path, smi=_smi(answer))
    assert out.strip() == f"build={expected}"


def test_llama_build_without_gpu_is_empty_with_a_reason(tmp_path):
    out = _sh('nvidia_info; llama_cuda_build 13 >/dev/null; llama_cuda_build 13; echo "why=$LLAMA_CUDA_WHY"', tmp_path)
    assert "why=no working NVIDIA GPU (nvidia-smi not found)" in out


def test_live_exec_streams_uv_lines_logs_everything_keeps_the_exit_code_and_beats(tmp_path):
    log = tmp_path / "install.log"
    body = f"""
LOG_FILE={log}; AF_HEARTBEAT=2; : >"$LOG_FILE"
rc=0
live_exec sh -c 'echo " Downloading torch (1.9GiB)"; echo " + torch==2.13.0"; sleep 5; echo "Installed 3 packages"; exit 7' || rc=$?
echo "rc=$rc"
"""
    out = _sh(body, tmp_path)
    assert "    | Downloading torch (1.9GiB)" in out
    assert "torch==2.13.0" not in out  # package lists stay in the log
    assert re.search(r"\.\.\. still working \(0m 0[2-5]s elapsed; last: Downloading torch \(1\.9GiB\)\)", out), out
    assert "    | Installed 3 packages" in out
    assert out.strip().endswith("rc=7")
    logged = log.read_text()
    assert " + torch==2.13.0" in logged and "Installed 3 packages" in logged


def test_the_gateway_install_and_the_llama_swap_run_live():
    text = SCRIPT.read_text()
    assert 'RUN_LIVE=1 RUN_SOFT="$_gsoft" run "install abstractgateway' in text
    assert "RUN_LIVE=1 RUN_SOFT=1 run \"install llama.cpp's $_lb build\"" in text


def test_gpu_step_keeps_the_cuda_build_only_when_it_offloads():
    text = SCRIPT.read_text()
    step = text[text.index('step "NVIDIA GPU check"'):]
    step = step[: step.index("\nfi\n\n")]
    # The check loads llama.cpp the way AbstractCore does (its preload first), then asks for offload.
    assert "prepare_llama_cpp_import()" in step and "llama_supports_gpu_offload()" in step
    keep = step.index('[ "$(smoke_val "$_r" offload)" = 1 ]')
    back = step.index("reinstall llama.cpp's cpu build")
    assert keep < back
    assert '--find-links "$GGUF_LINKS"' in step[back:]
