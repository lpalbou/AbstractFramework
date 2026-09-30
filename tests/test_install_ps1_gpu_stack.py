"""install.ps1, the gpu setting on Windows + NVIDIA (root backlog 0988).

No Windows or NVIDIA hardware is needed: a fake `nvidia-smi`, a fake `uv` and a fake Python stand in
for them, and the installer's functions are loaded from the script's AST (running the script would
install). Needs PowerShell 7 (`pwsh`); skipped without it (CI's ubuntu and windows runners have it).

What is covered here:
- the stack decision from `nvidia-smi --query-gpu=driver_version,compute_cap,name` (CUDA 13 / CUDA 12 /
  CPU, the reason printed), including errors, old drivers and several GPUs;
- how PyTorch's build is selected (`--torch-backend`, or the explicit index with +cuXXX pins);
- the llama.cpp fallback order CUDA -> vulkan -> cpu -> none, with a fake uv that installs builds and
  a fake Python whose smoke answer depends on the installed build;
- live progress: output streamed as it comes, a heartbeat with the elapsed time and the last
  Downloading line, package lines counted, every line in the log, the exit code kept, arguments with
  spaces and quotes passed intact;
- the -Print plan for each stack.

What is not (needs real hardware): that the CUDA wheels really load and offload on an NVIDIA GPU.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install.ps1"
LLAMA = "https://abetlen.github.io/llama-cpp-python/whl"

pytestmark = pytest.mark.skipif(shutil.which("pwsh") is None, reason="needs PowerShell 7 (pwsh)")

FUNCTIONS = [
    "Write-Info", "Write-Ok", "Write-Warn2", "Get-NvidiaInfo", "Select-GpuStack", "Get-TorchSelection",
    "ConvertTo-WinArg", "Invoke-LiveProcess", "Invoke-Smoke", "Resolve-LlamaBuild", "Test-TorchReinstall",
]
VARIABLES = ["AfTorchIndex", "AfTorchPins", "AfLlamaSizes", "AfLlamaSmoke"]


def _loader() -> str:
    script = str(SCRIPT).replace("'", "''")
    names = ", ".join(f"'{n}'" for n in FUNCTIONS)
    variables = ", ".join(f"'{n}'" for n in VARIABLES)
    return f"""
$ast = [System.Management.Automation.Language.Parser]::ParseFile('{script}', [ref]$null, [ref]$null)
$names = @({names})
foreach ($f in $ast.FindAll({{ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $names -contains $n.Name }}, $true)) {{ Invoke-Expression $f.Extent.Text }}
$vars = @({variables})
foreach ($a in $ast.EndBlock.Statements) {{
    if ($a -is [System.Management.Automation.Language.AssignmentStatementAst] -and $a.Left -is [System.Management.Automation.Language.VariableExpressionAst] -and $vars -contains $a.Left.VariablePath.UserPath) {{ Invoke-Expression $a.Extent.Text }}
}}
$script:HeartbeatSeconds = 15
"""


def _pwsh(body: str, tmp_path: Path, *, path_prefix: Path | None = None) -> str:
    env = {k: v for k, v in os.environ.items() if not k.upper().endswith(("_KEY", "_TOKEN"))}
    env.update({"HOME": str(tmp_path), "USERPROFILE": str(tmp_path), "TERM": "dumb", "NO_COLOR": "1"})
    # The real nvidia-smi (if any) never answers: only the fake one on PATH, or none.
    env["PATH"] = os.pathsep.join(
        ([str(path_prefix)] if path_prefix else []) + [os.path.dirname(shutil.which("pwsh")), "/usr/bin", "/bin"]
    )
    proc = subprocess.run(["pwsh", "-NoProfile", "-Command", _loader() + body], capture_output=True, text=True,
                          env=env, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout


def _exe(path: Path, text: str) -> Path:
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def _fake_smi(tmp_path: Path, *, with_cc: str | None, without_cc: str | None = None, exit_code: int = 0) -> Path:
    """A fake nvidia-smi: `with_cc` answers the driver_version,compute_cap,name query (None = that
    query fails, like a driver too old for compute_cap); `without_cc` answers driver_version,name."""
    fake = tmp_path / "fakebin"
    fake.mkdir(exist_ok=True)
    lines = [
        "#!/bin/sh",
        f"[ {exit_code} -ne 0 ] && {{ echo 'NVIDIA-SMI has failed because it could not communicate with the NVIDIA driver.'; exit {exit_code}; }}",
        'case "$*" in',
        f"  *compute_cap*) {'printf %b ' + repr(with_cc) if with_cc is not None else 'echo \"Field compute_cap is not a valid field to query.\"; exit 2'};;",
        f"  *) printf %b {repr(without_cc or '')};;",
        "esac",
    ]
    _exe(fake / "nvidia-smi", "\n".join(lines) + "\n")
    return fake


def _stack(tmp_path: Path, fake: Path | None) -> dict:
    out = _pwsh(
        "$i = Get-NvidiaInfo; $s = Select-GpuStack $i\n"
        "[ordered]@{ ok = $i.Ok; driver = $i.Driver; cc = $i.Cc; error = $i.Error; name = $s.Name; torch = $s.Torch;"
        " llama = @($s.Llama); label = $s.Label; why = $s.Why } | ConvertTo-Json -Compress",
        tmp_path, path_prefix=fake,
    )
    return json.loads(out.strip().splitlines()[-1])


# --- the stack decision ---------------------------------------------------------------------------

def test_driver_580_and_compute_75_pick_cuda_13(tmp_path: Path) -> None:
    s = _stack(tmp_path, _fake_smi(tmp_path, with_cc="581.29, 8.9, NVIDIA GeForce RTX 4090\n"))
    assert (s["name"], s["torch"], s["llama"]) == ("cu130", "cu130", ["cu130", "vulkan", "cpu"])
    assert s["why"] == "NVIDIA GeForce RTX 4090, driver 581.29 (580 or newer) and compute capability 8.9 (7.5 or newer)"


def test_exactly_the_floors_pick_cuda_13(tmp_path: Path) -> None:
    s = _stack(tmp_path, _fake_smi(tmp_path, with_cc="580.00, 7.5, Tesla T4\n"))
    assert s["name"] == "cu130"


def test_driver_below_580_picks_cuda_12(tmp_path: Path) -> None:
    s = _stack(tmp_path, _fake_smi(tmp_path, with_cc="566.36, 8.6, NVIDIA GeForce RTX 3060\n"))
    assert (s["name"], s["torch"], s["llama"]) == ("cu126", "cu126", ["cu125", "vulkan", "cpu"])
    assert "not CUDA 13: driver 566.36 is older than 580" in s["why"]


def test_new_driver_on_an_old_gpu_picks_cuda_12(tmp_path: Path) -> None:
    s = _stack(tmp_path, _fake_smi(tmp_path, with_cc="581.29, 6.1, NVIDIA GeForce GTX 1080\n"))
    assert s["name"] == "cu126"
    assert "not CUDA 13: compute capability 6.1 is below 7.5" in s["why"]


def test_compute_capability_just_below_the_floor_picks_cuda_12(tmp_path: Path) -> None:
    # Volta (7.0) with a new driver: CUDA 13 builds need compute capability 7.5 or newer.
    s = _stack(tmp_path, _fake_smi(tmp_path, with_cc="581.29, 7.0, Tesla V100-SXM2-16GB\n"))
    assert s["name"] == "cu126"
    assert "not CUDA 13: compute capability 7.0 is below 7.5" in s["why"]


@pytest.mark.parametrize(
    "action, state, tag, expected",
    [
        ("install", "@{}", "cu130", False),                    # a first install has nothing to replace
        ("upgrade", "@{}", "cu130", True),                     # before 0.6.3 no TORCH= was recorded: PyPI's CPU build
        ("upgrade", "@{}", "", False),                         # CPU before, CPU now
        ("upgrade", "@{ TORCH = '' }", "cu130", True),         # CPU -> CUDA 13 (driver updated)
        ("upgrade", "@{ TORCH = 'cu126' }", "cu130", True),    # CUDA 12 -> CUDA 13
        ("upgrade", "@{ TORCH = 'cu130' }", "", True),         # CUDA 13 -> CPU (GPU removed)
        ("upgrade", "@{ TORCH = 'cu130' }", "cu130", False),   # same stack: keep torch
        ("repair", "@{ TORCH = 'cu130' }", "cu126", True),
    ],
)
def test_torch_is_reinstalled_only_when_the_stack_changes(tmp_path: Path, action, state, tag, expected) -> None:
    out = _pwsh(f"$st = {state}; if (Test-TorchReinstall '{action}' $st '{tag}') {{ 'YES' }} else {{ 'NO' }}", tmp_path)
    assert out.strip().splitlines()[-1] == ("YES" if expected else "NO")


def test_several_gpus_are_judged_by_the_oldest(tmp_path: Path) -> None:
    fake = _fake_smi(tmp_path, with_cc="581.29, 8.9, NVIDIA GeForce RTX 4090\n581.29, 6.1, NVIDIA GeForce GTX 1080\n")
    s = _stack(tmp_path, fake)
    assert s["cc"] == 6.1 and s["name"] == "cu126"


def test_driver_that_cannot_report_compute_capability_uses_the_driver_alone(tmp_path: Path) -> None:
    s = _stack(tmp_path, _fake_smi(tmp_path, with_cc=None, without_cc="531.14, NVIDIA GeForce RTX 2080\n"))
    assert s["ok"] is True and s["cc"] is None and s["name"] == "cu126"


def test_driver_below_525_is_cpu_with_a_reason(tmp_path: Path) -> None:
    s = _stack(tmp_path, _fake_smi(tmp_path, with_cc="516.94, 7.5, Quadro RTX 4000\n"))
    assert (s["name"], s["torch"], s["llama"]) == ("cpu", "", ["vulkan", "cpu"])
    assert "older than 525" in s["why"] and "update the NVIDIA driver" in s["why"]


def test_no_nvidia_smi_is_cpu(tmp_path: Path) -> None:
    s = _stack(tmp_path, None)
    assert s["ok"] is False and s["error"] == "nvidia-smi not found"
    assert (s["name"], s["torch"], s["llama"]) == ("cpu", "", ["vulkan", "cpu"])
    assert s["why"].startswith("no working NVIDIA GPU (nvidia-smi not found)")


def test_failing_nvidia_smi_is_cpu_and_says_why(tmp_path: Path) -> None:
    s = _stack(tmp_path, _fake_smi(tmp_path, with_cc="", exit_code=9))
    assert s["ok"] is False and s["name"] == "cpu"
    assert "could not communicate with the NVIDIA driver" in s["error"]


def test_garbage_from_nvidia_smi_is_cpu(tmp_path: Path) -> None:
    s = _stack(tmp_path, _fake_smi(tmp_path, with_cc="No devices were found\n"))
    assert s["ok"] is False and s["name"] == "cpu"


# --- PyTorch's build --------------------------------------------------------------------------------

def test_torch_selection_uses_the_backend_flag_or_the_index_with_exact_pins(tmp_path: Path) -> None:
    out = _pwsh(
        "@{ backend = Get-TorchSelection 'cu130' $true; index = Get-TorchSelection 'cu126' $false; none = Get-TorchSelection '' $true }"
        " | ConvertTo-Json -Depth 4 -Compress",
        tmp_path,
    )
    got = json.loads(out.strip().splitlines()[-1])
    assert got["backend"] == {"Args": ["--torch-backend", "cu130"], "Constraints": []}
    assert got["index"]["Args"] == ["--index", "https://download.pytorch.org/whl/cu126", "--index-strategy", "unsafe-best-match"]
    assert got["index"]["Constraints"] == ["torch==2.14.0+cu126", "torchvision==0.29.0+cu126", "torchaudio==2.11.0+cu126"]
    assert got["none"] == {"Args": [], "Constraints": []}


# --- llama.cpp fallback order, with a fake uv and a fake Python -------------------------------------

def _llama_fakes(tmp_path: Path, *, fail_install: set[str], smoke: dict[str, dict]) -> tuple[Path, Path, Path]:
    """uv records its calls and "installs" the build named by --find-links into state.txt (or fails
    for builds in `fail_install`); python answers the smoke for the build in state.txt."""
    fake = tmp_path / "fakebin"
    fake.mkdir(exist_ok=True)
    state = tmp_path / "state.txt"
    calls = tmp_path / "uv-calls.txt"
    fails = " ".join(sorted(fail_install)) or "none"
    _exe(fake / "uv", f"""#!/bin/sh
echo "$*" >> '{calls}'
if [ "$1 $2" = "pip uninstall" ]; then rm -f '{state}'; exit 0; fi
build=$(echo "$*" | sed -n 's#.*/whl/\\([a-z0-9]*\\)/llama-cpp-python/.*#\\1#p')
for f in {fails}; do [ "$f" = "$build" ] && {{ echo "error: no matching distribution for $build" >&2; exit 1; }}; done
echo " Downloading llama-cpp-python ($build)" >&2
echo "$build" > '{state}'
echo " + llama-cpp-python==0.3.35" >&2
exit 0
""")
    answers = "\n".join(
        f"  {b}) echo 'AFSMOKE {json.dumps(r)}';;" for b, r in smoke.items()
    )
    _exe(fake / "python", f"""#!/bin/sh
b=$(cat '{state}' 2>/dev/null)
case "$b" in
{answers}
  *) echo 'AFSMOKE {{"import": false, "offload": false, "error": "ModuleNotFoundError: No module named llama_cpp"}}';;
esac
""")
    return fake, state, calls


def _resolve(tmp_path: Path, fake: Path, variants: list[str], installed: str) -> tuple[dict, str]:
    log = tmp_path / "install.log"
    body = f"""
$script:LogFile = '{log}'
$uv = '{fake / "uv"}'; $py = '{fake / "python"}'
$r = Resolve-LlamaBuild -Variants @({", ".join(repr(v) for v in variants)}) -Installed '{installed}' -Install {{
    param($v)
    $code = Invoke-LiveProcess -Exe $uv -Arguments @('pip', 'install', '--python', $py, '--no-index', '--find-links', "https://abetlen.github.io/llama-cpp-python/whl/$v/llama-cpp-python/", 'llama-cpp-python==0.3.35') -Log $script:LogFile
    $code -eq 0
}} -Check {{ param($v) Invoke-Smoke $py $AfLlamaSmoke $script:LogFile }} -Remove {{
    Invoke-LiveProcess -Exe $uv -Arguments @('pip', 'uninstall', '--python', $py, 'llama-cpp-python') -Log $script:LogFile | Out-Null
}}
"RESULT " + (@{{ kept = $r.Kept; where = $r.Where; why = @($r.Why) }} | ConvertTo-Json -Compress)
"""
    out = _pwsh(body, tmp_path)
    line = [l for l in out.splitlines() if l.startswith("RESULT ")][-1]
    return json.loads(line[7:]), out


GPU_OK = {"import": True, "offload": True, "version": "0.3.35"}
CPU_ONLY = {"import": True, "offload": False, "version": "0.3.35"}
NO_DLL = {"import": False, "offload": False, "error": "FileNotFoundError: Could not find module llama.dll (or one of its dependencies)"}


def test_cuda_build_that_offloads_is_kept(tmp_path: Path) -> None:
    fake, state, calls = _llama_fakes(tmp_path, fail_install=set(), smoke={"cu130": GPU_OK})
    state.write_text("cu130\n")  # the gateway install already included it
    got, out = _resolve(tmp_path, fake, ["cu130", "vulkan", "cpu"], "cu130")
    assert got == {"kept": "cu130", "where": "GPU offload", "why": []}
    assert not calls.exists(), "nothing is reinstalled when the included build works"
    assert "llama.cpp 0.3.35 (cu130 build): loads, GPU offload" in out


def test_cuda_build_without_its_dlls_falls_back_to_vulkan(tmp_path: Path) -> None:
    fake, state, calls = _llama_fakes(tmp_path, fail_install=set(), smoke={"cu130": NO_DLL, "vulkan": GPU_OK})
    state.write_text("cu130\n")
    got, out = _resolve(tmp_path, fake, ["cu130", "vulkan", "cpu"], "cu130")
    assert got["kept"] == "vulkan" and got["where"] == "GPU offload"
    assert got["why"] == [f"cu130: does not load: {NO_DLL['error']}"]
    assert "llama.cpp cu130 build does not load: FileNotFoundError" in out and "trying the next build" in out
    assert "llama.cpp: installing its vulkan build (about 45 MB)" in out
    assert [l.split("/whl/")[1].split("/")[0] for l in calls.read_text().splitlines()] == ["vulkan"]
    assert "--no-index" in calls.read_text()


def test_order_is_cuda_then_vulkan_then_cpu(tmp_path: Path) -> None:
    fake, state, calls = _llama_fakes(tmp_path, fail_install={"vulkan"}, smoke={"cu130": CPU_ONLY, "cpu": CPU_ONLY})
    state.write_text("cu130\n")
    got, out = _resolve(tmp_path, fake, ["cu130", "vulkan", "cpu"], "cu130")
    # A GPU build that loads without GPU offload is not kept; the cpu build is kept when it loads.
    assert got == {"kept": "cpu", "where": "CPU", "why": ["cu130: loads, but reports no GPU offload", "vulkan: did not install"]}
    assert [l.split("/whl/")[1].split("/")[0] for l in calls.read_text().splitlines()] == ["vulkan", "cpu"]


def test_no_build_loads_removes_llama_cpp(tmp_path: Path) -> None:
    fake, state, calls = _llama_fakes(tmp_path, fail_install=set(), smoke={"cu125": NO_DLL, "vulkan": NO_DLL, "cpu": NO_DLL})
    got, out = _resolve(tmp_path, fake, ["cu125", "vulkan", "cpu"], "")
    assert got["kept"] == "" and len(got["why"]) == 3
    assert calls.read_text().splitlines()[-1].startswith("pip uninstall --python ")
    assert not state.exists(), "a llama.cpp that cannot load is never left installed"


def test_nothing_installed_nothing_removed(tmp_path: Path) -> None:
    fake, state, calls = _llama_fakes(tmp_path, fail_install={"vulkan", "cpu"}, smoke={})
    got, _ = _resolve(tmp_path, fake, ["vulkan", "cpu"], "")
    assert got["kept"] == "" and got["why"] == ["vulkan: did not install", "cpu: did not install"]
    assert "uninstall" not in calls.read_text()


# --- live progress --------------------------------------------------------------------------------

def test_live_process_streams_lines_beats_counts_logs_and_keeps_the_exit_code(tmp_path: Path) -> None:
    fake = tmp_path / "fakebin"
    fake.mkdir()
    prog = _exe(fake / "slow", """#!/bin/sh
for a in "$@"; do echo "ARG[$a]"; done
echo "Resolved 257 packages in 3.1s" >&2
echo " Downloading torch (1.9GiB)" >&2
sleep 3
echo " + torch==2.14.0+cu130" >&2
echo " + numpy==2.5.3" >&2
echo "Installed 257 packages in 12s" >&2
exit 3
""")
    log = tmp_path / "live.log"
    body = f"""
$script:HeartbeatSeconds = 1
$code = Invoke-LiveProcess -Exe '{prog}' -Arguments @('plain', 'with space', 'quote"inside', 'C:\\dir with space\\', '') -Log '{log}'
"EXIT $code"
"""
    out = _pwsh(body, tmp_path)
    assert "EXIT 3" in out
    # Arguments reach the program intact (Windows command-line quoting, as .NET splits it).
    for arg in ("ARG[plain]", "ARG[with space]", 'ARG[quote"inside]', "ARG[C:\\dir with space\\]", "ARG[]"):
        assert f"    | {arg}" in out, out
    assert "    | Resolved 257 packages in 3.1s" in out and "    | Downloading torch (1.9GiB)" in out.replace("|  ", "| ")
    # While torch downloads nothing is printed: the heartbeat says how long and what it is doing.
    beats = [l for l in out.splitlines() if "still working" in l]
    assert beats, out
    # A beat may fire before the first line arrives on a loaded machine (no `last:` yet); the
    # beats during the download name it.
    assert any(re.search(r"\.\.\. still working \(\d+s elapsed; last: Downloading torch \(1\.9GiB\)\)", b) for b in beats), beats
    # Package lines go to the log only, counted on the console.
    assert "torch==2.14.0+cu130" not in out and "    | (2 package lines: see the log)" in out
    logged = log.read_text()
    assert " + torch==2.14.0+cu130" in logged and "Installed 257 packages" in logged and "ARG[with space]" in logged


def test_live_process_is_quiet_for_fast_commands(tmp_path: Path) -> None:
    fake = tmp_path / "fakebin"
    fake.mkdir()
    prog = _exe(fake / "fast", "#!/bin/sh\necho done\n")
    out = _pwsh(f"$c = Invoke-LiveProcess -Exe '{prog}' -Arguments @() -Log ''; \"EXIT $c\"", tmp_path)
    assert "    | done" in out and "still working" not in out and "EXIT 0" in out


# --- the -Print plan for each stack -----------------------------------------------------------------

def _print(tmp_path: Path, fake: Path | None, profile: str = "gpu") -> str:
    env = {k: v for k, v in os.environ.items() if not k.upper().endswith(("_KEY", "_TOKEN"))}
    env.update({"HOME": str(tmp_path), "USERPROFILE": str(tmp_path), "LOCALAPPDATA": str(tmp_path / "lad"),
                "PROCESSOR_ARCHITECTURE": "AMD64", "TERM": "dumb"})
    env["PATH"] = os.pathsep.join(([str(fake)] if fake else []) + [os.path.dirname(shutil.which("pwsh")), "/usr/bin", "/bin"])
    argv = ["pwsh", "-NoProfile", "-File", str(SCRIPT), "-Print", "-Profile", profile, "-Port", "18999"]
    proc = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not (tmp_path / "lad").exists(), "-Print must not write anything"
    return proc.stdout


def _install_line(out: str) -> str:
    return next(l for l in out.splitlines() if " tool install " in l and "abstractgateway" in l)


def test_print_cuda_13_plan(tmp_path: Path) -> None:
    out = _print(tmp_path, _fake_smi(tmp_path, with_cc="581.29, 8.9, NVIDIA GeForce RTX 4090\n"))
    assert "+ GPU stack: CUDA 13 (NVIDIA GeForce RTX 4090, driver 581.29 (580 or newer) and compute capability 8.9 (7.5 or newer))" in out
    install = _install_line(out)
    assert f"--find-links {LLAMA}/cu130/llama-cpp-python/ --torch-backend cu130 " in install
    assert "large downloads ahead: PyTorch CUDA 13 build (about 1.9 GB), llama.cpp cu130 build (about 220 MB)" in out
    assert "llama.cpp builds tried in this order: cu130 (about 220 MB), then vulkan (about 45 MB), then cpu (about 7 MB)" in out
    assert "  GPU stack:  CUDA 13 (" in out
    # aec-audio-processing has Windows wheels: not dropped any more (0988).
    assert "aec-audio-processing; sys_platform == 'never'" not in out and "--no-build-package aec-audio-processing" not in install


def test_print_cuda_12_plan(tmp_path: Path) -> None:
    out = _print(tmp_path, _fake_smi(tmp_path, with_cc="560.94, 8.6, NVIDIA GeForce RTX 3080\n"))
    install = _install_line(out)
    assert f"--find-links {LLAMA}/cu125/llama-cpp-python/ --torch-backend cu126 " in install
    assert "PyTorch CUDA 12 build (about 2.5 GB), llama.cpp cu125 build (about 480 MB)" in out


def test_print_no_nvidia_plan_uses_pypi_torch_and_vulkan_first(tmp_path: Path) -> None:
    out = _print(tmp_path, None)
    install = _install_line(out)
    assert "--torch-backend" not in install and "--index " not in install
    assert f"--find-links {LLAMA}/vulkan/llama-cpp-python/ " in install
    assert "+ GPU stack: CPU (no working NVIDIA GPU (nvidia-smi not found)" in out
    assert "llama.cpp builds tried in this order: vulkan (about 45 MB), then cpu (about 7 MB)" in out


def test_print_light_profile_is_unchanged(tmp_path: Path) -> None:
    out = _print(tmp_path, _fake_smi(tmp_path, with_cc="581.29, 8.9, NVIDIA GeForce RTX 4090\n"), profile="light")
    install = _install_line(out)
    assert "--torch-backend" not in install and f"--find-links {LLAMA}/cpu/llama-cpp-python/ " in install
    assert "GPU stack" not in out and "large downloads ahead" not in out


def test_install_steps_use_live_output_and_the_fallbacks_are_wired() -> None:
    """Static wiring the dry run cannot show (the script refuses a real install off Windows)."""
    ps1 = SCRIPT.read_text(encoding="utf-8")
    # The gateway install and every llama.cpp swap stream their output.
    assert "-Shown $shownInstall -Soft:$Soft -Live -IndexPins $indexPins)" in ps1
    assert "'--refresh-package', 'llama-cpp-python', \"llama-cpp-python==$ggufPin\") -Soft -Live" in ps1
    # CUDA install fails -> without llama.cpp -> PyTorch's CPU build (and CUDA llama builds dropped).
    a = ps1.index("attempt: PyTorch $($stack.Label) build with the llama.cpp $ggufVariant build")
    b = ps1.index("attempt: PyTorch $($stack.Label) build without llama.cpp")
    c = ps1.index("falling back to PyTorch's CPU build")
    assert a < b < c
    assert ps1.count("$llamaVariants = @($llamaVariants | Where-Object { $_ -notlike 'cu*' })") == 2
    # A CUDA torch that does not import is replaced by the CPU build; one that imports without CUDA is kept.
    assert "does not import ($why): replacing it with PyTorch's CPU build" in ps1
    assert "installed, but CUDA is not available" in ps1
    # A CPU-only torch after a CUDA build was requested is said out loud.
    assert "is a CPU-only build although the $($stack.Label) build ($($stack.Torch)) was requested" in ps1
    assert "if (Test-TorchReinstall $action $state $torchTag) { $script:TorchReinstall = $true }" in ps1
    # A stack change replaces torch's packages; the stack is recorded for the next run.
    assert "if ($script:TorchReinstall) { foreach ($p in $AfTorchPins.Keys) { $argv += @('--reinstall-package', $p) } }" in ps1
    assert '"TORCH=$(if ($script:TorchSel.Args.Count) { $stack.Torch })", "LLAMA=$llamaFinal"' in ps1
    # An older uv without `uv tool install --torch-backend` gets the explicit index.
    assert "-match '--torch-backend'" in ps1
