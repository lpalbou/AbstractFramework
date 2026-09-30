"""PyPI index lag right after a release never drops a feature (root backlog 0987 item 28).

Operator requirement (2026-09-30): "the upgrade should never fail; if there is a lag or delay, it
should auto retry." On the Linux box the 0.7.1 upgrade got uv's "there is no version of
abstractgateway[gpu]==0.8.1" from a lagging PyPI mirror, and the installer's voice fallback then
installed without local voice. Now a failure is index lag only when uv exits 1 with its resolution
failure header and names a package the installer pinned exactly in uv's empty-version form; then the
SAME install (voice, llama.cpp included) runs again after 15, 30, 60, 120... s, and after about
10 minutes it stops with the cause instead of installing less.

A fake `uv` stands in for the real one and a fake `sleep` records the waits (install.sh runs under
sh and dash); install.ps1's Invoke-Native is loaded from the script's AST and driven with the same
fake uv under PowerShell 7 (skipped without pwsh).
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
SH = ROOT / "scripts" / "install.sh"
PS1 = ROOT / "scripts" / "install.ps1"
TEXT = SH.read_text(encoding="utf-8")
GW_PIN = re.search(r'^AF_GATEWAY_PIN_DEFAULT="([^"]+)"', TEXT, re.M).group(1)
MATRIX = dict(c.split("==", 1) for c in re.search(r'^AF_PY_MATRIX="([^"]+)"', TEXT, re.M).group(1).split())
VOICE_PIN = MATRIX["abstractvoice"]
DELAYS = ["15", "30", "60", "120", "120", "120", "120"]

# uv's resolution failures, as uv 0.11 prints them (the graphical form, wrapped at 80 columns) and
# as the Linux box's log had it (the "error:/cause:" form).
LAG_GATEWAY = f"""  × No solution found when resolving dependencies:
  ╰─▶ Because there is no version of abstractgateway[gpu,tray]=={GW_PIN} and
      you require abstractgateway[gpu,tray]=={GW_PIN}, we can conclude that your
      requirements are unsatisfiable."""
LAG_GATEWAY_PLAIN = f"""error: No solution found when resolving dependencies
cause: Because there is no version of abstractgateway[gpu]=={GW_PIN} and you require abstractgateway[gpu]=={GW_PIN}, we can conclude that your requirements are unsatisfiable."""
LAG_CORE = f"""  × No solution found when resolving dependencies:
  ╰─▶ Because there is no version of abstractcore=={MATRIX['abstractcore']} and
      abstractgateway=={GW_PIN} depends on abstractcore=={MATRIX['abstractcore']}, we can conclude
      that abstractgateway=={GW_PIN} cannot be used.
      And because you require abstractgateway[tray]=={GW_PIN}, we can conclude
      that your requirements are unsatisfiable."""
# "no version of" is wrapped onto two lines here: the match must join them.
LAG_RUNTIME_WRAPPED = f"""  × No solution found when resolving dependencies:
  ╰─▶ Because there is no version
      of abstractruntime=={MATRIX['AbstractRuntime']} and you require abstractruntime=={MATRIX['AbstractRuntime']}, we
      can conclude that your requirements are unsatisfiable."""
LAG_VOICE = f"""  × No solution found when resolving dependencies:
  ╰─▶ Because there is no version of abstractvoice[supertonic]=={VOICE_PIN} and
      you require abstractvoice[supertonic]=={VOICE_PIN}, we can conclude that your
      requirements are unsatisfiable."""
# The index already lists the new version but the file host does not serve its file yet: uv exits 2
# (uv 0.11.14's exact output against an index listing a file that answers 404).
F404_GATEWAY = f"""error: Failed to fetch: `https://files.pythonhosted.org/packages/9a/1c/0f/abstractgateway-{GW_PIN}-py3-none-any.whl`
  Caused by: HTTP status client error (404 Not Found) for url (https://files.pythonhosted.org/packages/9a/1c/0f/abstractgateway-{GW_PIN}-py3-none-any.whl)"""
F404_RUNTIME_SDIST = f"""error: Failed to fetch: `https://files.pythonhosted.org/packages/77/ab/abstractruntime-{MATRIX['AbstractRuntime']}.tar.gz`
  Caused by: HTTP status client error (404 Not Found) for url (https://files.pythonhosted.org/packages/77/ab/abstractruntime-{MATRIX['AbstractRuntime']}.tar.gz)"""
# Not lag: a 404 for a file the installer did not pin (a dependency's), and a 404 without uv's fetch failure.
F404_OTHER = """error: Failed to fetch: `https://files.pythonhosted.org/packages/11/22/onnxruntime-1.22.0-cp312-cp312-manylinux_2_27_x86_64.whl`
  Caused by: HTTP status client error (404 Not Found) for url (https://files.pythonhosted.org/packages/11/22/onnxruntime-1.22.0-cp312-cp312-manylinux_2_27_x86_64.whl)"""
# Not lag: a platform without the voice engine's wheels (a real conflict), and a pin that is not
# the installer's release pin (an older gateway version than the one pinned).
NO_WHEEL = f"""  × No solution found when resolving dependencies:
  ╰─▶ Because onnxruntime==1.22.0 has no wheels with a matching platform tag
      and abstractvoice[supertonic]=={VOICE_PIN} depends on onnxruntime>=1.20, we can
      conclude that abstractvoice[supertonic]=={VOICE_PIN} cannot be used.
      And because you require abstractvoice[supertonic]=={VOICE_PIN}, we can conclude
      that your requirements are unsatisfiable."""
NO_HEADER = f"""error: Because there is no version of abstractgateway=={GW_PIN} and you require abstractgateway=={GW_PIN}."""
OTHER_VERSION = f"""  × No solution found when resolving dependencies:
  ╰─▶ Because there is no version of abstractgateway=={GW_PIN}0 and you require
      abstractgateway=={GW_PIN}0, we can conclude that your requirements are unsatisfiable."""


def _exe(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def _fake_uv(fake: Path, tmp_path: Path, *, fail_first: int, message: str, exit_code: int = 1,
             fail_when: str = "") -> Path:
    """`uv tool install` fails the first FAIL_FIRST times with MESSAGE on stderr (only when its
    arguments contain FAIL_WHEN, if given), then installs a gateway command that starts."""
    tool_bin = tmp_path / "toolbin"
    (tmp_path / "uv-message.txt").write_text(message + "\n", encoding="utf-8")
    return _exe(fake / "uv", f"""#!/bin/sh
echo "$*" >> "{tmp_path}/uv-calls.log"
case "$1 $2" in
  "--version "*) echo "uv 0.0.0" ;;
  "tool dir") echo "{tool_bin}" ;;
  "tool install")
    n=$(cat "{tmp_path}/uv-count" 2>/dev/null || echo 0)
    hit=1
    if [ -n "{fail_when}" ]; then hit=0; for a in "$@"; do case "$a" in *"{fail_when}"*) hit=1 ;; esac; done; fi
    if [ "$hit" = 1 ] && [ "$n" -lt {fail_first} ]; then
        echo $((n + 1)) > "{tmp_path}/uv-count"
        cat "{tmp_path}/uv-message.txt" >&2
        exit {exit_code}
    fi
    mkdir -p "{tool_bin}" && printf "#!/bin/sh\\nexit 0\\n" > "{tool_bin}/abstractgateway" && chmod +x "{tool_bin}/abstractgateway" ;;
esac
exit 0
""")


def _fake_sleep(fake: Path, tmp_path: Path) -> None:
    """Records the installer's waits; live_exec's 1 s polling passes through (shortened)."""
    real = shutil.which("sleep")
    _exe(fake / "sleep", f"""#!/bin/sh
case "$1" in 1) exec {real} 0.1 ;; esac
echo "$1" >> "{tmp_path}/slept.log"
""")


def _run_sh(shell: str, tmp_path: Path, *, fail_first: int, message: str, extra: tuple[str, ...] = (),
            exit_code: int = 1, fail_when: str = "") -> tuple[subprocess.CompletedProcess[str], list[str], list[str]]:
    if shutil.which(shell) is None:
        pytest.skip(f"needs {shell}")
    fake = tmp_path / "fakebin"
    fake.mkdir()
    _exe(fake / "xcode-select", "#!/bin/sh\nexit 2\n")
    _fake_uv(fake, tmp_path, fail_first=fail_first, message=message, exit_code=exit_code, fail_when=fail_when)
    _fake_sleep(fake, tmp_path)
    env = {"HOME": str(tmp_path), "PATH": f"{fake}:/usr/bin:/bin:/usr/sbin:/sbin", "TERM": "dumb",
           "XDG_DATA_HOME": str(tmp_path / "data")}
    proc = subprocess.run(
        [shell, str(SH), "--profile", "light", "--port", "18996", "--no-start", "--no-service", "--no-open",
         "--no-modify-path", "--no-console", *extra],
        capture_output=True, text=True, env=env, timeout=300,
    )
    calls = tmp_path / "uv-calls.log"
    installs = [line for line in calls.read_text().splitlines() if line.startswith("tool install ")] if calls.exists() else []
    slept_file = tmp_path / "slept.log"
    slept = slept_file.read_text().split() if slept_file.exists() else []
    return proc, installs, slept


SHELLS = ["sh", "dash"]
VOICE_ARG = f"abstractvoice[supertonic,stt]=={VOICE_PIN}"


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("message", [LAG_GATEWAY, LAG_GATEWAY_PLAIN, LAG_CORE, LAG_RUNTIME_WRAPPED, LAG_VOICE],
                         ids=["gateway", "gateway-plain", "core-constraint", "runtime-wrapped", "voice"])
def test_install_sh_retries_the_same_full_install_through_index_lag(tmp_path: Path, shell: str, message: str) -> None:
    proc, installs, slept = _run_sh(shell, tmp_path, fail_first=2, message=message)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out
    # Three runs of the SAME command: nothing dropped between them (voice, llama.cpp wheel if any).
    assert len(installs) == 3, installs
    assert installs[0] == installs[1] == installs[2]
    assert VOICE_ARG in installs[0]
    assert slept == ["15", "30"]
    lag = re.search(r"there is no version\s+of (\S+?)(\[[^\]]*\])?==(\S+?) ", " ".join(message.split())).groups()
    name = {"abstractruntime": "AbstractRuntime"}.get(lag[0], lag[0])
    version = lag[2]
    assert f"PyPI hasn't published {name} {version} to every mirror yet; retrying in 15 s (attempt 2/8)" in proc.stdout
    assert f"PyPI hasn't published {name} {version} to every mirror yet; retrying in 30 s (attempt 3/8)" in proc.stdout
    assert "retrying without it" not in out
    assert "Voice:      Supertonic (text-to-speech) and Whisper (speech-to-text), local on CPU" in proc.stdout
    assert "did not succeed" not in out


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("message,name,version", [(F404_GATEWAY, "abstractgateway", GW_PIN),
                                                  (F404_RUNTIME_SDIST, "AbstractRuntime", MATRIX["AbstractRuntime"])],
                         ids=["gateway-wheel", "runtime-sdist"])
def test_install_sh_retries_when_the_new_file_is_not_served_yet(tmp_path: Path, shell: str, message: str, name: str, version: str) -> None:
    proc, installs, slept = _run_sh(shell, tmp_path, fail_first=2, message=message, exit_code=2)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out
    assert len(installs) == 3 and len(set(installs)) == 1, installs
    assert VOICE_ARG in installs[0]
    assert slept == ["15", "30"]
    assert f"PyPI hasn't published {name} {version} to every mirror yet; retrying in 15 s (attempt 2/8)" in proc.stdout
    assert "retrying without it" not in out


def test_install_sh_a_404_for_a_file_it_did_not_pin_is_not_lag(tmp_path: Path) -> None:
    proc, installs, slept = _run_sh("sh", tmp_path, fail_first=99, message=F404_OTHER, exit_code=2)
    assert slept == []
    assert "PyPI hasn't published" not in proc.stdout
    assert "retrying without it" in proc.stdout


@pytest.mark.parametrize("shell", SHELLS)
def test_install_sh_index_lag_beyond_the_budget_fails_clearly_and_drops_nothing(tmp_path: Path, shell: str) -> None:
    proc, installs, slept = _run_sh(shell, tmp_path, fail_first=99, message=LAG_GATEWAY)
    assert proc.returncode != 0
    assert len(installs) == 8 and len(set(installs)) == 1, installs
    assert VOICE_ARG in installs[0]
    assert slept == DELAYS
    assert f"PyPI still does not list abstractgateway {GW_PIN} after 8 attempts over about 10 minutes" in proc.stderr
    assert "run the installer again in a few minutes; it installs everything, local voice included" in proc.stderr
    out = proc.stdout + proc.stderr
    assert "retrying without it" not in out and "Voice:      skipped" not in out
    assert "(attempt 8/8)" in proc.stdout


@pytest.mark.parametrize("shell", SHELLS)
def test_install_sh_a_platform_without_voice_wheels_still_falls_back_without_waiting(tmp_path: Path, shell: str) -> None:
    proc, installs, slept = _run_sh(shell, tmp_path, fail_first=99, message=NO_WHEEL, fail_when="abstractvoice[")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert slept == []
    assert "local voice (Supertonic, Whisper) did not install on this system: retrying without it" in proc.stdout
    assert "Voice:      skipped: its packages did not install on this system" in proc.stdout
    assert VOICE_ARG in installs[0] and "abstractvoice[" not in installs[-1]
    assert "PyPI hasn't published" not in proc.stdout


@pytest.mark.parametrize("message,exit_code", [(OTHER_VERSION, 1), (LAG_GATEWAY, 2), (NO_HEADER, 1)],
                         ids=["unpinned-version", "exit-2", "no-resolution-header"])
def test_install_sh_only_uvs_exact_pin_form_with_exit_1_is_lag(tmp_path: Path, message: str, exit_code: int) -> None:
    """A version the installer did not pin, or uv's exit 2 (an error, not a resolution failure), is not
    lag: the existing handling runs (here: the voice fallback, then a clear failure), no waiting."""
    proc, installs, slept = _run_sh("sh", tmp_path, fail_first=99, message=message, exit_code=exit_code)
    assert slept == []
    assert "PyPI hasn't published" not in proc.stdout
    assert proc.returncode != 0
    assert "retrying without it" in proc.stdout


def test_install_sh_pin_latest_has_no_exact_pins_to_wait_for(tmp_path: Path) -> None:
    proc, installs, slept = _run_sh("sh", tmp_path, fail_first=99, message=LAG_GATEWAY, extra=("--pin", "latest"))
    assert slept == [] and proc.returncode != 0
    assert "PyPI hasn't published" not in proc.stdout
    assert "abstractvoice[supertonic,stt]" in installs[0] and VOICE_ARG not in installs[0]  # no matrix: no voice pin


def test_install_sh_verbose_still_classifies_lag(tmp_path: Path) -> None:
    proc, installs, slept = _run_sh("sh", tmp_path, fail_first=1, message=LAG_GATEWAY, extra=("-v",))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert slept == ["15"] and len(installs) == 2 and installs[0] == installs[1]


def test_install_sh_print_shows_the_voice_requirement_with_its_matrix_pin(tmp_path: Path) -> None:
    proc = subprocess.run(["sh", str(SH), "--print", "--profile", "light", "--port", "18996"], capture_output=True,
                          text=True, env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "TERM": "dumb"})
    assert proc.returncode == 0, proc.stderr
    assert f"--with '{VOICE_ARG}' " in proc.stdout


# --- install.ps1 ------------------------------------------------------------------------------

needs_pwsh = pytest.mark.skipif(shutil.which("pwsh") is None, reason="needs PowerShell 7 (pwsh)")
PS_FUNCTIONS = ["Write-Info", "Write-Ok", "Write-Warn2", "Stop-Install", "Format-Arg", "Format-Cmd", "ConvertTo-WinArg",
                "Invoke-LiveProcess", "Invoke-Native", "Find-IndexLag", "Read-LogFrom", "Get-VoiceRequirement"]


def _ps(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _pwsh_native(tmp_path: Path, *, fail_first: int, message: str, soft: bool, exit_code: int = 1,
                 pins: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    fake = tmp_path / "fakebin"
    fake.mkdir()
    uv = _fake_uv(fake, tmp_path, fail_first=fail_first, message=message, exit_code=exit_code)
    pins = [f"abstractgateway=={GW_PIN}", *(f"{k}=={v}" for k, v in MATRIX.items())] if pins is None else pins
    names = ", ".join(_ps(n) for n in PS_FUNCTIONS)
    body = f"""
$ast = [System.Management.Automation.Language.Parser]::ParseFile({_ps(str(PS1))}, [ref]$null, [ref]$null)
$names = @({names})
foreach ($f in $ast.FindAll({{ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $names -contains $n.Name }}, $true)) {{ Invoke-Expression $f.Extent.Text }}
foreach ($a in $ast.EndBlock.Statements) {{
    if ($a -is [System.Management.Automation.Language.AssignmentStatementAst] -and $a.Left.Extent.Text -in @('$script:IndexRetryDelays', '$AfPyMatrix')) {{ Invoke-Expression $a.Extent.Text }}
}}
$script:HeartbeatSeconds = 15
$script:DryRun = $false
$script:Twins = New-Object System.Collections.Generic.List[string]
$script:LogFile = {_ps(str(tmp_path / "install.log"))}
function Test-Net {{ return $true }}
$global:slept = @()
function Start-Sleep {{ param([int]$Seconds, [int]$Milliseconds) if ($Seconds) {{ $global:slept += $Seconds }} else {{ [System.Threading.Thread]::Sleep($Milliseconds) }} }}
$voice = Get-VoiceRequirement 'abstractvoice[supertonic,stt]' $true
$argv = @({_ps(str(uv))}, 'tool', 'install', '--with', $voice, 'abstractgateway[tray]=={GW_PIN}')
try {{
    $ok = Invoke-Native -Description 'install abstractgateway' -Argv $argv -Live -Soft:${'true' if soft else 'false'} -IndexPins @({", ".join(_ps(p) for p in pins)})
    Write-Host "RESULT=$ok"
}} catch {{ Write-Host "THROWN=$($_.Exception.Message)" }}
Write-Host "SLEPT=$($global:slept -join ',')"
"""
    env = {k: v for k, v in os.environ.items() if not k.upper().endswith(("_KEY", "_TOKEN", "PASSWORD"))}
    env.update({"HOME": str(tmp_path), "USERPROFILE": str(tmp_path), "TERM": "dumb", "NO_COLOR": "1"})
    return subprocess.run(["pwsh", "-NoProfile", "-Command", body], capture_output=True, text=True, env=env, timeout=180)


def _installs(tmp_path: Path) -> list[str]:
    return [line for line in (tmp_path / "uv-calls.log").read_text().splitlines() if line.startswith("tool install ")]


@needs_pwsh
@pytest.mark.parametrize("message", [LAG_GATEWAY, LAG_CORE, LAG_RUNTIME_WRAPPED, LAG_VOICE],
                         ids=["gateway", "core-constraint", "runtime-wrapped", "voice"])
def test_install_ps1_retries_the_same_install_through_index_lag(tmp_path: Path, message: str) -> None:
    proc = _pwsh_native(tmp_path, fail_first=2, message=message, soft=True)
    out = proc.stdout + proc.stderr
    assert "RESULT=True" in out, out
    assert "SLEPT=15,30" in out
    installs = _installs(tmp_path)
    assert len(installs) == 3 and len(set(installs)) == 1
    assert VOICE_ARG in installs[0]
    assert "to every mirror yet; retrying in 15 s (attempt 2/8)" in out
    assert "to every mirror yet; retrying in 30 s (attempt 3/8)" in out
    assert "did not succeed" not in out


@needs_pwsh
@pytest.mark.parametrize("message", [F404_GATEWAY, F404_RUNTIME_SDIST], ids=["gateway-wheel", "runtime-sdist"])
def test_install_ps1_retries_when_the_new_file_is_not_served_yet(tmp_path: Path, message: str) -> None:
    proc = _pwsh_native(tmp_path, fail_first=2, message=message, soft=True, exit_code=2)
    out = proc.stdout + proc.stderr
    assert "RESULT=True" in out, out
    assert "SLEPT=15,30" in out
    installs = _installs(tmp_path)
    assert len(installs) == 3 and len(set(installs)) == 1
    assert "to every mirror yet; retrying in 15 s (attempt 2/8)" in out


@needs_pwsh
def test_install_ps1_index_lag_beyond_the_budget_throws_even_when_soft(tmp_path: Path) -> None:
    proc = _pwsh_native(tmp_path, fail_first=99, message=LAG_GATEWAY, soft=True)
    out = proc.stdout + proc.stderr
    assert f"THROWN=AFBOOT: install abstractgateway failed: PyPI still does not list abstractgateway {GW_PIN} after 8 attempts over about 10 minutes" in out, out
    assert "SLEPT=" + ",".join(DELAYS) in out
    assert len(_installs(tmp_path)) == 8
    assert "RESULT=" not in out


@needs_pwsh
@pytest.mark.parametrize("message,exit_code", [(NO_WHEEL, 1), (OTHER_VERSION, 1), (LAG_GATEWAY, 2), (NO_HEADER, 1), (F404_OTHER, 2)],
                         ids=["no-wheel", "unpinned-version", "exit-2", "no-resolution-header", "404-unpinned-file"])
def test_install_ps1_other_failures_keep_the_soft_fallback(tmp_path: Path, message: str, exit_code: int) -> None:
    proc = _pwsh_native(tmp_path, fail_first=99, message=message, soft=True, exit_code=exit_code)
    out = proc.stdout + proc.stderr
    assert "RESULT=False" in out, out
    assert "SLEPT=\n" in out or out.rstrip().endswith("SLEPT=")
    assert len(_installs(tmp_path)) == 1
    assert "PyPI hasn't published" not in out


@needs_pwsh
def test_install_ps1_without_pins_nothing_is_lag(tmp_path: Path) -> None:
    proc = _pwsh_native(tmp_path, fail_first=99, message=LAG_GATEWAY, soft=True, pins=[])
    out = proc.stdout + proc.stderr
    assert "RESULT=False" in out and len(_installs(tmp_path)) == 1, out


def test_install_ps1_wires_the_index_pins_like_install_sh() -> None:
    ps1 = PS1.read_text(encoding="utf-8")
    assert "$script:IndexRetryDelays = @(" + ", ".join(DELAYS) + ")" in ps1
    assert f'AF_INDEX_RETRY_DELAYS="{" ".join(DELAYS)}"' in TEXT
    assert "-Soft:$Soft -Live -IndexPins $indexPins)" in ps1
    assert "if (-not $From -and $Pin -ne 'latest') { $indexPins += \"abstractgateway==$Pin\" }" in ps1
    assert "if ($isRelease) { $indexPins += $AfPyMatrix }" in ps1
    assert "(Get-VoiceRequirement $voice.Spec $isRelease)" in ps1
    assert 'RUN_INDEX_RETRY=1 run "install abstractgateway' in TEXT
