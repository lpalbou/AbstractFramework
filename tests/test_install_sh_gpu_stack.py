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
    "answer, torch_cuda, sees, expected",
    [
        ("595.91.07, 7.5, Quadro RTX 5000", "13", "1", "cu130"),
        ("595.91.07, 7.5, Quadro RTX 5000", "12", "1", "cu125"),
        ("560.35, 8.6, RTX 3090", "12", "1", "cu125"),
        ("560.35, 8.6, RTX 3090", "13", "1", ""),  # CUDA 13 torch needs driver 580+
        ("516.94, 8.6, RTX 3060", "12", "1", ""),  # CUDA 12 needs 525+
        ("595.91.07, 7.5, Quadro RTX 5000", "", "0", ""),  # CPU torch
        ("595.91.07, 7.5, Quadro RTX 5000", "13", "0", ""),  # torch does not see the GPU
        (None, "13", "1", "cu130"),  # no nvidia-smi (container, WSL): PyTorch's CUDA decides
    ],
)
def test_llama_build_follows_torch_cuda_and_the_driver(tmp_path, answer, torch_cuda, sees, expected):
    # Called the way install.sh calls it: in this shell, results in variables.
    out = _sh(f'nvidia_info; llama_cuda_build "{torch_cuda}" {sees}; echo "build=$LLAMA_CUDA_BUILD why=$LLAMA_CUDA_WHY"',
              tmp_path, smi=None if answer is None else _smi(answer))
    build, why = out.strip().split(" why=", 1)
    assert build == f"build={expected}"
    assert (why == "") == bool(expected), why


def test_llama_build_is_never_called_in_a_subshell():
    # A $(...) call drops LLAMA_CUDA_WHY and `set -u` aborts the install where it is printed.
    assert "$(llama_cuda_build" not in SCRIPT.read_text()


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


# --- the real GPU check block, run end to end with fakes (not the functions alone) ------------------

def _gpu_block() -> str:
    """The Linux gpu check exactly as install.sh runs it (from `GPU_RESULT=""` to its closing `fi`)."""
    text = SCRIPT.read_text()
    start = text.index('GPU_RESULT=""; TORCH_RESULT=""')
    end = text.index("\nfi\n", text.index('step "NVIDIA GPU check"', start)) + 4
    return text[start:end]


_FAKE_PY = """#!/bin/sh
f="$1"
if grep -q 'import torch' "$f"; then
  echo "AFSMOKE version=2.11.0+cu130"; echo "AFSMOKE cuda_build=$FAKE_TORCH_CUDA"; echo "AFSMOKE cuda=$FAKE_TORCH_SEES"
  [ "$FAKE_TORCH_SEES" = 1 ] && echo "AFSMOKE device=Fake GPU"
elif grep -q 'find_spec("llama_cpp")' "$f"; then echo "AFSMOKE cuda_build=0"
elif grep -q 'import llama_cpp' "$f"; then echo "AFSMOKE import=1"; echo "AFSMOKE version=0.3.35"; echo "AFSMOKE offload=1"
elif grep -q 'best_faster_whisper_device' "$f"; then echo "AFSMOKE device=cpu"
fi
exit 0
"""


def _run_gpu_block(tmp_path: Path, *, smi: str | None, torch_cuda: str = "13.0", torch_sees: str = "1",
                   glibc: str = "2.39") -> tuple[int, str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    if smi is not None:
        _exe(bindir / "nvidia-smi", smi)
    _exe(bindir / "ldd", f'#!/bin/sh\necho "ldd (GNU libc) {glibc}"\n')
    venv = tmp_path / "venv"
    (venv / "bin").mkdir(parents=True, exist_ok=True)
    _exe(venv / "bin" / "python", _FAKE_PY)
    runs = tmp_path / "runs.txt"
    log = tmp_path / "install.log"
    log.write_text("")
    prelude = "\n".join([
        "set -eu",
        'C_D=""; C_0=""',
        'step() { echo "STEP $*"; }; ok() { echo "OK $*"; }; warn() { echo "WARN $*"; }; info() { echo "INFO $*"; }',
        f'run() {{ echo "RUN $*" >>"{runs}"; RUN_RC=0; }}',
        f'tool_venv() {{ TOOL_VENV="{venv}"; TOOL_VENV2=""; }}',
        _function("have"),
        _assignments("AF_LLAMA_CUDA13", "AF_LLAMA_CUDA12"),
        _function("nvidia_info"),
        _function("llama_cuda_build"),
        _function("torch_driver_hint"),
        'AF_LLAMA_INDEX=https://example.invalid; PROFILE=gpu; OS_ID=linux; PRINT=0; UV=uv',
        f'LOG_FILE="{log}"; TMPDIR="{tmp_path}"',
        'GGUF_PIN=0.3.35; GGUF_LINKS=https://example.invalid/cpu',
        'GGUF_RESULT="llama-cpp-python 0.3.35 (cpu wheel from https://example.invalid/cpu)"',
        'VOICE_SPEC=v; VOICE_RESULT="Supertonic and Whisper, local on CPU"',
    ])
    body = _gpu_block() + '\necho "END GGUF_RESULT=$GGUF_RESULT"\necho "END TORCH_RESULT=$TORCH_RESULT"\n'
    env = {"PATH": f"{bindir}:/usr/bin:/bin", "HOME": str(tmp_path), "LC_ALL": "C",
           "FAKE_TORCH_CUDA": torch_cuda, "FAKE_TORCH_SEES": torch_sees}
    shell = shutil.which("dash") or "/bin/sh"
    proc = subprocess.run([shell, "-c", prelude + "\n" + body], capture_output=True, text=True, env=env, timeout=60)
    return proc.returncode, proc.stdout + proc.stderr, runs.read_text() if runs.exists() else ""


def test_gpu_block_completes_when_nvidia_smi_is_missing_but_torch_sees_the_gpu(tmp_path):
    # Containers without NVML, WSL: the install must go on to the console/start/summary steps.
    rc, out, runs = _run_gpu_block(tmp_path, smi=None)
    assert rc == 0, out
    assert "END GGUF_RESULT=llama-cpp-python 0.3.35 (cu130 CUDA build" in out, out
    assert "cu130/llama-cpp-python/" in runs


def test_gpu_block_keeps_the_cpu_build_with_its_reason_when_torch_sees_no_gpu(tmp_path):
    rc, out, runs = _run_gpu_block(tmp_path, smi=None, torch_sees="0")
    assert rc == 0, out
    assert "INFO llama.cpp keeps its CPU build: PyTorch does not see the GPU" in out
    assert "END GGUF_RESULT=llama-cpp-python 0.3.35 (cpu wheel from https://example.invalid/cpu); CPU (PyTorch does not see the GPU" in out
    assert "cu130" not in runs


def test_gpu_block_names_old_glibc_instead_of_trying_the_cuda_wheel(tmp_path):
    rc, out, runs = _run_gpu_block(tmp_path, smi=_smi("595.91.07, 7.5, Quadro RTX 5000"), glibc="2.31")
    assert rc == 0, out
    assert "llama.cpp's CUDA builds need glibc 2.35 or newer (this system has glibc 2.31)" in out
    assert "cu130" not in runs


def test_gpu_block_driver_hint_only_when_the_driver_is_too_old(tmp_path):
    (tmp_path / "old").mkdir()
    (tmp_path / "new").mkdir()
    rc, out, _ = _run_gpu_block(tmp_path / "old", smi=_smi("560.35, 8.6, RTX 3090"), torch_sees="0")
    assert rc == 0, out
    assert "(CUDA 13.0 needs NVIDIA driver 580 or newer; this one is 560.35)" in out
    rc, out, _ = _run_gpu_block(tmp_path / "new", smi=_smi("595.91.07, 7.5, Quadro RTX 5000"), torch_sees="0")
    assert rc == 0, out
    assert "WARN PyTorch: torch 2.11.0+cu130 (CUDA 13.0) does not see the GPU" in out and "needs NVIDIA driver" not in out


def test_live_exec_ctrl_c_stops_the_background_command(tmp_path):
    # Non-interactive sh starts background jobs with SIGINT ignored: without live_exec's trap,
    # Ctrl-C ended the installer and left uv running.
    import signal
    import time

    log = tmp_path / "install.log"
    log.write_text("")
    pidfile = tmp_path / "child.pid"
    prelude = "\n".join(["set -eu", 'C_D=""; C_0=""', _function("live_exec")])
    body = f'LOG_FILE={log}; AF_HEARTBEAT=60\nlive_exec sh -c \'echo $$ > {pidfile}; exec sleep 30\'\necho after'
    shell = shutil.which("dash") or "/bin/sh"
    proc = subprocess.Popen([shell, "-c", prelude + "\n" + body], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(50):
        if pidfile.exists() and pidfile.read_text().strip():
            break
        time.sleep(0.1)
    child = int(pidfile.read_text().strip())
    time.sleep(0.5)
    proc.send_signal(signal.SIGINT)
    out, _ = proc.communicate(timeout=20)
    time.sleep(0.3)
    try:
        os.kill(child, 0)
        alive = True
    except ProcessLookupError:
        alive = False
    if alive:
        os.kill(child, signal.SIGKILL)
    assert not alive, "the background command survived Ctrl-C"
    assert proc.returncode == 130, out
    assert "after" not in out
