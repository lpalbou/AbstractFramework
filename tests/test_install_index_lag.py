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
# The index already lists the new version but the file host does not serve its file yet (uv 0.11.14's
# wording, captured against a local index answering 404; the URLs are PyPI-shaped). Exit 1 when the
# metadata was served and only the wheel answers 404 (the PyPI case), exit 2 when the metadata file
# answers 404 too.
_H = "packages/4f/04/1c/9e8e2f1a404d1b1c2f3d6a4c3f0bd2e8f3a6c1d0e9b8a7c6d5e4f3a2b1c0d9e8"
F404_GATEWAY_DOWNLOAD = f"""Resolved 1 package in 2ms
  × Failed to download `abstractgateway=={GW_PIN}`
  ├─▶ Failed to fetch:
  │   `https://files.pythonhosted.org/{_H}/abstractgateway-{GW_PIN}-py3-none-any.whl`
  ╰─▶ HTTP status client error (404 Not Found) for url
      (https://files.pythonhosted.org/{_H}/abstractgateway-{GW_PIN}-py3-none-any.whl)"""
F404_GATEWAY = f"""error: Failed to fetch: `https://files.pythonhosted.org/{_H}/abstractgateway-{GW_PIN}-py3-none-any.whl.metadata`
  Caused by: HTTP status client error (404 Not Found) for url (https://files.pythonhosted.org/{_H}/abstractgateway-{GW_PIN}-py3-none-any.whl.metadata)"""
F404_RUNTIME_SDIST = f"""error: Failed to fetch: `https://files.pythonhosted.org/{_H}/abstractruntime-{MATRIX['AbstractRuntime']}.tar.gz`
  Caused by: HTTP status client error (404 Not Found) for url (https://files.pythonhosted.org/{_H}/abstractruntime-{MATRIX['AbstractRuntime']}.tar.gz)"""
# Not lag: a 404 for a file the installer did not pin (a dependency's, or another version of a
# pinned package), a server error, and a failure whose URL merely contains "404" in its hash.
F404_OTHER = f"""error: Failed to fetch: `https://files.pythonhosted.org/{_H}/onnxruntime-1.22.0-cp312-cp312-manylinux_2_27_x86_64.whl`
  Caused by: HTTP status client error (404 Not Found) for url (https://files.pythonhosted.org/{_H}/onnxruntime-1.22.0-cp312-cp312-manylinux_2_27_x86_64.whl)"""
F404_OTHER_VERSION = f"""  × Failed to download `abstractgateway=={GW_PIN}0`
  ├─▶ Failed to fetch:
  │   `https://files.pythonhosted.org/{_H}/abstractgateway-{GW_PIN}0-py3-none-any.whl`
  ╰─▶ HTTP status client error (404 Not Found) for url
      (https://files.pythonhosted.org/{_H}/abstractgateway-{GW_PIN}0-py3-none-any.whl)"""
F503_GATEWAY = f"""  × Failed to download `abstractgateway=={GW_PIN}`
  ├─▶ Request failed after 3 retries in 10.9s
  ├─▶ Failed to fetch:
  │   `https://files.pythonhosted.org/{_H}/abstractgateway-{GW_PIN}-py3-none-any.whl`
  ╰─▶ HTTP status server error (503 Service Unavailable) for url
      (https://files.pythonhosted.org/{_H}/abstractgateway-{GW_PIN}-py3-none-any.whl)"""
RESET_WITH_404_IN_HASH = f"""error: Failed to fetch: `https://files.pythonhosted.org/{_H}/abstractgateway-{GW_PIN}-py3-none-any.whl`
  Caused by: Request failed after 3 retries
  Caused by: connection reset by peer"""
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
@pytest.mark.parametrize("message,exit_code,name,version", [(F404_GATEWAY_DOWNLOAD, 1, "abstractgateway", GW_PIN),
                                                            (F404_GATEWAY, 2, "abstractgateway", GW_PIN),
                                                            (F404_RUNTIME_SDIST, 2, "AbstractRuntime", MATRIX["AbstractRuntime"])],
                         ids=["gateway-wheel-exit-1", "gateway-metadata-exit-2", "runtime-sdist"])
def test_install_sh_retries_when_the_new_file_is_not_served_yet(tmp_path: Path, shell: str, message: str, exit_code: int, name: str, version: str) -> None:
    proc, installs, slept = _run_sh(shell, tmp_path, fail_first=2, message=message, exit_code=exit_code)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out
    assert len(installs) == 3 and len(set(installs)) == 1, installs
    assert VOICE_ARG in installs[0]
    assert slept == ["15", "30"]
    assert f"PyPI hasn't published {name} {version} to every mirror yet; retrying in 15 s (attempt 2/8)" in proc.stdout
    assert "retrying without it" not in out


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("message,exit_code", [(F404_OTHER, 2), (F404_OTHER_VERSION, 1)],
                         ids=["dependency-file", "other-version"])
def test_install_sh_other_download_failures_are_not_lag(tmp_path: Path, shell: str, message: str, exit_code: int) -> None:
    """A 404 for a file the installer did not pin is neither index lag nor a network failure: the
    existing handling (the voice fallback, then a clear failure), no waiting. (A 5xx or a connection
    reset is a network failure: test_install_sh_retries_the_same_full_install_through_network_failures.)"""
    proc, installs, slept = _run_sh(shell, tmp_path, fail_first=99, message=message, exit_code=exit_code)
    assert slept == []
    assert "PyPI hasn't published" not in proc.stdout
    assert "retrying without it" in proc.stdout


def test_install_sh_a_file_still_not_served_after_the_budget_says_so(tmp_path: Path) -> None:
    proc, installs, slept = _run_sh("sh", tmp_path, fail_first=99, message=F404_GATEWAY_DOWNLOAD, exit_code=1)
    assert proc.returncode != 0
    assert len(installs) == 8 and len(set(installs)) == 1, installs
    assert f"PyPI lists abstractgateway {GW_PIN} but still does not serve its file after 8 attempts over about 10 minutes (uv: HTTP 404 fetching abstractgateway {GW_PIN})" in proc.stderr
    assert "retrying without it" not in proc.stdout + proc.stderr


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
    assert ("local voice (Supertonic, Whisper) did not install on this system (onnxruntime==1.22.0 has no wheels with a matching "
            "platform tag): retrying without it") in proc.stdout
    assert "Voice:      skipped: its packages did not install on this system: onnxruntime==1.22.0 has no wheels" in proc.stdout
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
    assert "a network error while downloading" not in proc.stdout
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
                "Invoke-LiveProcess", "Invoke-Native", "Find-IndexLag", "Read-LogFrom", "Get-VoiceRequirement",
                "ConvertTo-RetryText", "Get-RetryCause", "Find-Transient", "Find-CargoRetry"]
PS_ASSIGNMENTS = ["$script:IndexRetryDelays", "$AfPyMatrix", "$script:UvDeterministic", "$script:UvTransient", "$script:CargoLag",
                  "$script:CargoDeterministic", "$script:CargoTransient"]


def _ps(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _pwsh_native(tmp_path: Path, *, fail_first: int, message: str, soft: bool, exit_code: int = 1,
                 pins: list[str] | None = None, retry: str = "", cargo: bool = False) -> subprocess.CompletedProcess[str]:
    fake = tmp_path / "fakebin"
    fake.mkdir()
    uv = _fake_uv(fake, tmp_path, fail_first=fail_first, message=message, exit_code=exit_code)
    if cargo:
        _fake_cargo(fake, tmp_path, fail_first=fail_first, message=message)
    pins = [f"abstractgateway=={GW_PIN}", *(f"{k}=={v}" for k, v in MATRIX.items())] if pins is None else pins
    names = ", ".join(_ps(n) for n in PS_FUNCTIONS)
    body = f"""
$ast = [System.Management.Automation.Language.Parser]::ParseFile({_ps(str(PS1))}, [ref]$null, [ref]$null)
$names = @({names})
foreach ($f in $ast.FindAll({{ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $names -contains $n.Name }}, $true)) {{ Invoke-Expression $f.Extent.Text }}
foreach ($a in $ast.EndBlock.Statements) {{
    if ($a -is [System.Management.Automation.Language.AssignmentStatementAst] -and $a.Left.Extent.Text -in @({", ".join(_ps(a) for a in PS_ASSIGNMENTS)})) {{ Invoke-Expression $a.Extent.Text }}
}}
$script:RerunCmd = 'RERUN-THIS-COMMAND'

$script:HeartbeatSeconds = 15
$script:DryRun = $false
$script:Twins = New-Object System.Collections.Generic.List[string]
$script:LogFile = {_ps(str(tmp_path / "install.log"))}
function Test-Net {{ return $true }}
$global:slept = @()
function Start-Sleep {{ param([int]$Seconds, [int]$Milliseconds) if ($Seconds) {{ $global:slept += $Seconds }} else {{ [System.Threading.Thread]::Sleep($Milliseconds) }} }}
$voice = Get-VoiceRequirement 'abstractvoice[supertonic,stt]' $true
$argv = @({_ps(str(uv))}, 'tool', 'install', '--with', $voice, 'abstractgateway[tray]=={GW_PIN}')
{"$argv = @(" + _ps(str(fake / "cargo")) + ", 'install', '--locked', '--force', 'abstractcode', '--version', '0.7.1')" if cargo else ""}
try {{
    $ok = Invoke-Native -Description 'install abstractgateway' -Argv $argv -Live -Soft:${'true' if soft else 'false'} -IndexPins @({", ".join(_ps(p) for p in ([] if cargo else pins))}){" -Retry " + retry if retry else ""}
    Write-Host "RESULT=$ok"
    Write-Host "GAVEUP=$($script:RunGaveUp)"
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
@pytest.mark.parametrize("message,exit_code", [(F404_GATEWAY_DOWNLOAD, 1), (F404_GATEWAY, 2), (F404_RUNTIME_SDIST, 2)],
                         ids=["gateway-wheel-exit-1", "gateway-metadata-exit-2", "runtime-sdist"])
def test_install_ps1_retries_when_the_new_file_is_not_served_yet(tmp_path: Path, message: str, exit_code: int) -> None:
    proc = _pwsh_native(tmp_path, fail_first=2, message=message, soft=True, exit_code=exit_code)
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
@pytest.mark.parametrize("message,exit_code", [(NO_WHEEL, 1), (OTHER_VERSION, 1), (LAG_GATEWAY, 2), (NO_HEADER, 1), (F404_OTHER, 2),
                                                (F404_OTHER_VERSION, 1)],
                         ids=["no-wheel", "unpinned-version", "exit-2", "no-resolution-header", "404-unpinned-file",
                              "404-other-version"])
def test_install_ps1_other_failures_keep_the_soft_fallback(tmp_path: Path, message: str, exit_code: int) -> None:
    proc = _pwsh_native(tmp_path, fail_first=99, message=message, soft=True, exit_code=exit_code)
    out = proc.stdout + proc.stderr
    assert "RESULT=False" in out, out
    assert "SLEPT=\n" in out or out.rstrip().endswith("SLEPT=")
    assert len(_installs(tmp_path)) == 1
    assert "PyPI hasn't published" not in out


@needs_pwsh
def test_install_ps1_a_file_still_not_served_after_the_budget_says_so(tmp_path: Path) -> None:
    proc = _pwsh_native(tmp_path, fail_first=99, message=F404_GATEWAY_DOWNLOAD, soft=True, exit_code=1)
    out = proc.stdout + proc.stderr
    assert f"THROWN=AFBOOT: install abstractgateway failed: PyPI lists abstractgateway {GW_PIN} but still does not serve its file after 8 attempts over about 10 minutes (uv: HTTP 404 fetching abstractgateway {GW_PIN})" in out, out
    assert len(_installs(tmp_path)) == 8


@needs_pwsh
def test_install_ps1_without_pins_nothing_is_lag(tmp_path: Path) -> None:
    proc = _pwsh_native(tmp_path, fail_first=99, message=LAG_GATEWAY, soft=True, pins=[])
    out = proc.stdout + proc.stderr
    assert "RESULT=False" in out and len(_installs(tmp_path)) == 1, out


def test_install_ps1_wires_the_index_pins_like_install_sh() -> None:
    ps1 = PS1.read_text(encoding="utf-8")
    assert "$script:IndexRetryDelays = @(" + ", ".join(DELAYS) + ")" in ps1
    assert f'AF_INDEX_RETRY_DELAYS="{" ".join(DELAYS)}"' in TEXT
    assert "-Soft:$Soft -Live -IndexPins $indexPins -Retry uv)" in ps1
    assert "if (-not $From -and $Pin -ne 'latest') { $indexPins += \"abstractgateway==$Pin\" }" in ps1
    assert "if ($isRelease) { $indexPins += $AfPyMatrix }" in ps1
    assert "(Get-VoiceRequirement $voice.Spec $isRelease)" in ps1
    assert 'RUN_INDEX_RETRY=1 run "install abstractgateway' in TEXT


# --- transient network failures (operator requirement 2026-09-30) -------------------------------
# "the upgrade should never fail; if there is a lag or delay, it should auto retry": a 502 while
# downloading torch made the installer take the voice fallback and finish green WITHOUT local voice
# (untracked/sweep-2026-09-30/adversary/installer-502-*). Now a network failure runs the SAME install
# again on the ladder, then stops (exit 1) with the cause and the command to run again.

# The adversary's capture (uv's plain "error:/Caused by:" form, exit 2).
TORCH_502 = """Resolved 210 packages in 3.2s
error: Failed to download `torch==2.8.0`
  Caused by: HTTP status server error (502 Bad Gateway) for url (https://files.pythonhosted.org/packages/torch-2.8.0-cp312-none-macosx_11_0_arm64.whl)"""
# Captured from uv 0.11.14 against a local index (UV_HTTP_RETRIES=1): a 502, a 429, a connection reset,
# a dead host (DNS), a closed port, and a wheel cut off mid-download (exit 1, uv's graphical form).
REAL_502 = """error: Request failed after 1 retry in 1.9s
  Caused by: Failed to fetch: `http://127.0.0.1:18773/files/abstractgateway-{pin}-py3-none-any.whl`
  Caused by: HTTP status server error (502 Bad Gateway) for url (http://127.0.0.1:18773/files/abstractgateway-{pin}-py3-none-any.whl)""".format(pin=GW_PIN)
REAL_429 = """error: Request failed after 1 retry in 1.6s
  Caused by: Failed to fetch: `http://127.0.0.1:18775/files/aftooly-1.0-py3-none-any.whl`
  Caused by: HTTP status client error (429 Too Many Requests) for url (http://127.0.0.1:18775/files/aftooly-1.0-py3-none-any.whl)"""
REAL_RESET = """error: Request failed after 1 retry in 1.6s
  Caused by: Failed to fetch: `http://127.0.0.1:18774/files/aftoolx-2.0-py3-none-any.whl`
  Caused by: error sending request for url (http://127.0.0.1:18774/files/aftoolx-2.0-py3-none-any.whl)
  Caused by: client error (SendRequest)
  Caused by: connection error
  Caused by: Connection reset by peer (os error 54)"""
REAL_DNS = """error: Request failed after 1 retry in 2.6s
  Caused by: Failed to fetch: `http://nonexistent-host.invalid/simple/aftoolx/`
  Caused by: error sending request for url (http://nonexistent-host.invalid/simple/aftoolx/)
  Caused by: client error (Connect)
  Caused by: dns error
  Caused by: failed to lookup address information: nodename nor servname provided, or not known"""
REAL_REFUSED = """error: Request failed after 1 retry in 1.2s
  Caused by: Failed to fetch: `http://127.0.0.1:9/simple/aftoolx/`
  Caused by: error sending request for url (http://127.0.0.1:9/simple/aftoolx/)
  Caused by: client error (Connect)
  Caused by: tcp connect error
  Caused by: Connection refused (os error 61)"""
REAL_TRUNCATED = """Resolved 1 package in 7ms
  × Failed to download `aftoolx==2.0`
  ├─▶ Failed to write to the distribution cache
  ├─▶ error decoding response body
  ├─▶ request or response body error
  ├─▶ error reading a body from connection
  ╰─▶ end of file before message length reached"""
# uv's own timeout message (uv 0.11.14's binary).
UV_TIMEOUT = "error: Failed to download distribution due to network timeout. Try increasing UV_HTTP_TIMEOUT (current value: 30s)."
TRANSIENT = {"torch-502": (TORCH_502, 2), "real-502": (REAL_502, 2), "429": (REAL_429, 2), "reset": (REAL_RESET, 2),
             "dns": (REAL_DNS, 2), "refused": (REAL_REFUSED, 2), "truncated": (REAL_TRUNCATED, 1), "timeout": (UV_TIMEOUT, 2),
             "503-graphical": (F503_GATEWAY, 1), "reset-404-in-hash": (RESET_WITH_404_IN_HASH, 2)}
# Deterministic: never retried (the existing handling).
HASH_MISMATCH = """error: Failed to download `onnxruntime==1.22.0`
  Caused by: Hash mismatch for `onnxruntime==1.22.0`"""
CRC = """  × Failed to download `llama-cpp-python==0.3.33`
  ├─▶ Failed to read from zip file
  ╰─▶ a computed CRC32 value did not match the expected value"""
BUILD_FAILED = """  × Failed to build `webrtcvad==2.0.10`
  ├─▶ The build backend returned an error
  ╰─▶ Call to `setuptools.build_meta.build_wheel` failed (exit status: 1)"""
DETERMINISTIC = {"no-wheel": (NO_WHEEL, 1), "404-dependency": (F404_OTHER, 2), "404-other-version": (F404_OTHER_VERSION, 1),
                 "hash": (HASH_MISMATCH, 2), "crc": (CRC, 1), "build": (BUILD_FAILED, 1), "no-header": (NO_HEADER, 1)}
# cargo 1.98 (captured: crates.io asked for an unknown version, a dead proxy, a local sparse index answering 502).
CARGO_LAG = "    Updating crates.io index\nerror: could not find `abstractcode` in registry `crates-io` with version `=0.7.1`"
CARGO_502 = """    Updating crates.io index
warning: spurious network error (1 try remaining): failed to get successful HTTP response from `https://index.crates.io/config.json` (151.101.2.137), got 502
body:
bad gateway
error: failed to get successful HTTP response from `https://index.crates.io/config.json` (151.101.2.137), got 502"""
CARGO_DEAD_PROXY = """    Updating crates.io index
warning: spurious network error (1 try remaining): [7] Couldn't connect to server (Failed to connect to 127.0.0.1 port 9 after 0 ms: Couldn't connect to server)
error: download of config.json failed

Caused by:
  [7] Couldn't connect to server (Failed to connect to 127.0.0.1 port 9 after 0 ms: Couldn't connect to server)"""
CARGO_COMPILE = "error[E0308]: mismatched types\nerror: could not compile `abstractcode` (bin \"abstractcode\") due to 1 previous error"


def _sh_classifier(tmp_path: Path, fn: str, message: str, rc: int | None = None) -> str:
    """Runs install.sh's own classifier functions (the block from AF_UV_DETERMINISTIC to cargo_retry,
    cut out of the script) on MESSAGE as a log, under dash when present."""
    start = TEXT.index("AF_UV_DETERMINISTIC=")
    end = TEXT.index("\n}\n", TEXT.index("cargo_retry() {")) + 3
    log = tmp_path / "log.txt"
    log.write_text("$ the command\n" + message + "\n", encoding="utf-8")
    script = tmp_path / "cls.sh"
    call = f'{fn} "{log}" 1' + (f" {rc}" if rc is not None else "")
    script.write_text(TEXT[start:end] + "\n" + call + "\n", encoding="utf-8")
    shell = "dash" if shutil.which("dash") else "sh"
    return subprocess.run([shell, str(script)], capture_output=True, text=True, check=True).stdout.strip()


@pytest.mark.parametrize("name", sorted(TRANSIENT))
def test_install_sh_classifies_uvs_network_failures_as_transient(tmp_path: Path, name: str) -> None:
    message, rc = TRANSIENT[name]
    cause = _sh_classifier(tmp_path, "uv_transient", message, rc)
    assert cause, name
    assert "│" not in cause and not cause.lower().startswith(("caused by", "error:")), cause


@pytest.mark.parametrize("name", sorted(DETERMINISTIC))
def test_install_sh_never_retries_a_deterministic_uv_failure(tmp_path: Path, name: str) -> None:
    message, rc = DETERMINISTIC[name]
    assert _sh_classifier(tmp_path, "uv_transient", message, rc) == ""


def test_install_sh_a_signal_is_not_a_network_failure(tmp_path: Path) -> None:
    assert _sh_classifier(tmp_path, "uv_transient", REAL_502, 130) == ""


@pytest.mark.parametrize("message,kind", [(CARGO_LAG, "lag"), (CARGO_502, "transient"), (CARGO_DEAD_PROXY, "transient"), (CARGO_COMPILE, "")],
                         ids=["registry-lag", "502", "dead-proxy", "compile-error"])
def test_install_sh_classifies_cargo_failures(tmp_path: Path, message: str, kind: str) -> None:
    out = _sh_classifier(tmp_path, "cargo_retry", message)
    assert (out.split(" ", 1)[0] if out else "") == kind, out
    if kind == "transient":
        assert "spurious network error" not in out


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("name", ["torch-502", "real-502", "reset", "truncated", "timeout"])
def test_install_sh_retries_the_same_full_install_through_network_failures(tmp_path: Path, shell: str, name: str) -> None:
    message, rc = TRANSIENT[name]
    proc, installs, slept = _run_sh(shell, tmp_path, fail_first=2, message=message, exit_code=rc)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out
    assert len(installs) == 3 and len(set(installs)) == 1, installs
    assert VOICE_ARG in installs[0]
    assert slept == ["15", "30"]
    assert "a network error while downloading (uv: " in proc.stdout and "retrying in 15 s (attempt 2/8)" in proc.stdout
    assert "retrying without it" not in out and "did not succeed" not in out
    assert "Voice:      Supertonic (text-to-speech) and Whisper (speech-to-text), local on CPU" in proc.stdout
    assert "NOT installed" not in out


@pytest.mark.parametrize("shell", SHELLS)
def test_install_sh_a_network_failure_beyond_the_budget_fails_loudly_and_changes_nothing(tmp_path: Path, shell: str) -> None:
    """The adversary's case, persistent: a 502 on torch for every attempt. Never the voice fallback:
    8 identical attempts, then exit 1 with the cause and the exact command to run again; no state
    written, no 'installed' line."""
    proc, installs, slept = _run_sh(shell, tmp_path, fail_first=99, message=TORCH_502, exit_code=2)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 1, out
    assert len(installs) == 8 and len(set(installs)) == 1, installs
    assert VOICE_ARG in installs[0]
    assert slept == DELAYS
    assert "a network error while downloading, still failing after 8 attempts over about 10 minutes (uv: HTTP status server error (502 Bad Gateway)" in proc.stderr
    assert "Nothing was left out and nothing was changed" in proc.stderr
    assert re.search(r"run the installer again:\n    sh \S*install\.sh --profile light --port 18996 --no-start --no-service --no-open --no-modify-path --no-console\n", proc.stderr), proc.stderr
    assert "retrying without it" not in out and "AbstractFramework is installed" not in out
    assert not list(tmp_path.rglob("bootstrap.env"))


def test_install_sh_a_network_failure_never_drops_the_llama_cpp_wheel(tmp_path: Path) -> None:
    """The llama.cpp wheel's soft fallback is for a missing wheel, never for the network."""
    proc, installs, slept = _run_sh("sh", tmp_path, fail_first=2, message=REAL_RESET, exit_code=2)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert len(set(installs)) == 1
    assert "GGUF (llama.cpp) skipped" not in proc.stdout or "llama-cpp-python==" not in installs[0]


@pytest.mark.parametrize("shell", SHELLS)
def test_install_sh_voice_fallback_says_in_red_that_voice_is_not_installed(tmp_path: Path, shell: str) -> None:
    """A deterministic incompatibility keeps the voice fallback, but never as a silent green: the
    reason in the warning, the summary's headline and its last lines, and bootstrap.env."""
    proc, installs, slept = _run_sh(shell, tmp_path, fail_first=99, message=NO_WHEEL, fail_when="abstractvoice[")
    out = proc.stdout
    assert proc.returncode == 0, out + proc.stderr
    assert slept == []
    why = f"onnxruntime==1.22.0 has no wheels with a matching platform tag"
    assert f"local voice (Supertonic, Whisper) did not install on this system ({why}): retrying without it" in out
    assert "AbstractFramework is installed (--no-start), but NOT everything was installed:" in out
    assert "AbstractFramework is installed (--no-start).\n" not in out
    tail = out.rstrip().splitlines()[-2:]
    assert tail[0] == "NOT installed:", tail
    assert tail[1].startswith(f"  local voice (Supertonic, Whisper): skipped: its packages did not install on this system: {why}"), tail
    state = next(tmp_path.rglob("bootstrap.env")).read_text()
    assert "\nVOICE_SPEC=\n" in state
    assert re.search(rf"^VOICE_SKIPPED=skipped: its packages did not install on this system: {re.escape(why)}", state, re.M), state


def test_install_sh_voice_installed_records_no_skip(tmp_path: Path) -> None:
    proc, installs, slept = _run_sh("sh", tmp_path, fail_first=0, message="")
    assert proc.returncode == 0
    state = next(tmp_path.rglob("bootstrap.env")).read_text()
    assert "\nVOICE_SKIPPED=\n" in state and "NOT installed" not in proc.stdout


# --- crates.io lag and network failures for the terminal console / abstractcode ------------------

def _fake_cargo(fake: Path, tmp_path: Path, *, fail_first: int, message: str) -> Path:
    """`cargo install ... NAME --version V` fails the first FAIL_FIRST times with MESSAGE, then writes
    <root>/bin/NAME answering `NAME V`."""
    (tmp_path / "cargo-message.txt").write_text(message + "\n", encoding="utf-8")
    return _exe(fake / "cargo", f"""#!/bin/sh
echo "$*" >> "{tmp_path}/cargo-calls.log"
[ "$1" = --version ] && {{ echo "cargo 1.98.0 (fake)"; exit 0; }}
root=""; ver=""; prev=""; name=""
for a in "$@"; do
  case "$prev" in --root) root="$a" ;; --version) ver="$a" ;; esac
  case "$a" in abstractgateway-console|abstractcode) name="$a" ;; esac
  prev="$a"
done
[ -n "$root" ] || root="${{CARGO_HOME:-$HOME/.cargo}}"
n=$(cat "{tmp_path}/cargo-count" 2>/dev/null || echo 0)
if [ "$n" -lt {fail_first} ]; then echo $((n + 1)) > "{tmp_path}/cargo-count"; cat "{tmp_path}/cargo-message.txt" >&2; exit 101; fi
mkdir -p "$root/bin"; printf '#!/bin/sh\\necho "%s %s"\\n' "$name" "$ver" > "$root/bin/$name"; chmod +x "$root/bin/$name"
exit 0
""")


def _run_sh_cargo(tmp_path: Path, *, fail_first: int, message: str) -> tuple[subprocess.CompletedProcess[str], list[str], list[str]]:
    fake = tmp_path / "fakebin"
    fake.mkdir()
    _exe(fake / "xcode-select", "#!/bin/sh\necho /Library/Developer/CommandLineTools\n")  # a C compiler (macOS)
    _exe(fake / "cc", "#!/bin/sh\nexit 0\n")  # a C compiler (Linux)
    _fake_uv(fake, tmp_path, fail_first=0, message="")
    _fake_cargo(fake, tmp_path, fail_first=fail_first, message=message)
    _fake_sleep(fake, tmp_path)
    env = {"HOME": str(tmp_path), "PATH": f"{fake}:/usr/bin:/bin:/usr/sbin:/sbin", "TERM": "dumb",
           "XDG_DATA_HOME": str(tmp_path / "data")}
    proc = subprocess.run(["sh", str(SH), "--profile", "light", "--port", "18996", "--no-start", "--no-service", "--no-open",
                           "--no-modify-path", "--no-code-cli"], capture_output=True, text=True, env=env, timeout=300)
    calls = tmp_path / "cargo-calls.log"
    builds = [line for line in calls.read_text().splitlines() if line.startswith("install ")] if calls.exists() else []
    slept_file = tmp_path / "slept.log"
    return proc, builds, (slept_file.read_text().split() if slept_file.exists() else [])


@pytest.mark.parametrize("message", [CARGO_LAG, CARGO_502], ids=["registry-lag", "502"])
def test_install_sh_retries_the_console_build_through_crates_io_lag_and_the_network(tmp_path: Path, message: str) -> None:
    proc, builds, slept = _run_sh_cargo(tmp_path, fail_first=2, message=message)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out
    assert len(builds) == 3 and len(set(builds)) == 1 and "abstractgateway-console" in builds[0], builds
    assert slept == ["15", "30"]
    assert "retrying in 15 s (attempt 2/8)" in proc.stdout
    assert "NOT installed" not in out


def test_install_sh_crates_io_lag_beyond_the_budget_is_red_and_exits_1(tmp_path: Path) -> None:
    proc, builds, slept = _run_sh_cargo(tmp_path, fail_first=99, message=CARGO_LAG)
    out = proc.stdout
    assert proc.returncode == 1, out + proc.stderr
    assert len(builds) == 8 and slept == DELAYS
    assert "crates.io hasn't listed it yet (could not find `abstractcode` in registry `crates-io` with version `=0.7.1`); retrying in 15 s" in out
    assert "was not built: crates.io has not listed it yet after 8 attempts over about 10 minutes" in out
    assert "but NOT everything was installed:" in out
    lines = out.rstrip().splitlines()
    assert "NOT installed:" in lines[-5:] and lines[-2].startswith("What to do: run the installer again"), lines[-6:]
    assert lines[-1].startswith("    sh ") and "install.sh --profile light" in lines[-1]


def test_install_sh_a_compile_error_is_not_retried(tmp_path: Path) -> None:
    proc, builds, slept = _run_sh_cargo(tmp_path, fail_first=99, message=CARGO_COMPILE)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert len(builds) == 1 and slept == []
    assert "Terminal:   not installed (the build failed" in proc.stdout


# --- install.ps1: the same rules ------------------------------------------------------------------

@needs_pwsh
@pytest.mark.parametrize("name", ["torch-502", "reset", "truncated", "dns", "503-graphical", "reset-404-in-hash"])
def test_install_ps1_retries_network_failures_and_never_takes_the_soft_path(tmp_path: Path, name: str) -> None:
    message, rc = TRANSIENT[name]
    proc = _pwsh_native(tmp_path, fail_first=2, message=message, soft=True, exit_code=rc)
    out = proc.stdout + proc.stderr
    assert "RESULT=True" in out, out
    assert "SLEPT=15,30" in out
    assert len(_installs(tmp_path)) == 3 and len(set(_installs(tmp_path))) == 1
    assert "a network error while downloading (uv: " in out and "retrying in 15 s (attempt 2/8)" in out


@needs_pwsh
def test_install_ps1_a_network_failure_beyond_the_budget_throws_even_when_soft(tmp_path: Path) -> None:
    proc = _pwsh_native(tmp_path, fail_first=99, message=TORCH_502, soft=True, exit_code=2)
    out = proc.stdout + proc.stderr
    assert "THROWN=AFBOOT: install abstractgateway failed: a network error while downloading, still failing after 8 attempts over about 10 minutes (uv: HTTP status server error (502 Bad Gateway)" in out, out
    assert "run the installer again:\n    RERUN-THIS-COMMAND" in out
    assert "SLEPT=" + ",".join(DELAYS) in out and len(_installs(tmp_path)) == 8
    assert "RESULT=" not in out


@needs_pwsh
def test_install_ps1_retries_network_failures_without_pins_too(tmp_path: Path) -> None:
    """-Pin latest has no exact pins, but a network failure is still retried (-Retry uv)."""
    proc = _pwsh_native(tmp_path, fail_first=1, message=REAL_RESET, soft=True, exit_code=2, pins=[], retry="uv")
    out = proc.stdout + proc.stderr
    assert "RESULT=True" in out and "SLEPT=15" in out, out


@needs_pwsh
@pytest.mark.parametrize("name", sorted(DETERMINISTIC))
def test_install_ps1_never_retries_a_deterministic_failure(tmp_path: Path, name: str) -> None:
    message, rc = DETERMINISTIC[name]
    proc = _pwsh_native(tmp_path, fail_first=99, message=message, soft=True, exit_code=rc, retry="uv")
    out = proc.stdout + proc.stderr
    assert "RESULT=False" in out and len(_installs(tmp_path)) == 1, out
    assert "a network error while downloading" not in out


@needs_pwsh
@pytest.mark.parametrize("message,fails,result,gaveup", [(CARGO_LAG, 2, "True", ""), (CARGO_502, 2, "True", ""),
                                                        (CARGO_LAG, 99, "False", "crates.io has not listed it yet after 8 attempts"),
                                                        (CARGO_DEAD_PROXY, 99, "False", "a network error while downloading from crates.io"),
                                                        (CARGO_COMPILE, 99, "False", "")],
                         ids=["lag-then-ok", "502-then-ok", "lag-budget", "network-budget", "compile-error"])
def test_install_ps1_retries_cargo_through_crates_io_lag_and_the_network(tmp_path: Path, message: str, fails: int, result: str, gaveup: str) -> None:
    proc = _pwsh_native(tmp_path, fail_first=fails, message=message, soft=True, retry="cargo", cargo=True)
    out = proc.stdout + proc.stderr
    assert f"RESULT={result}" in out, out
    gave = next(line for line in out.splitlines() if line.startswith("GAVEUP="))
    assert (gaveup in gave) if gaveup else gave == "GAVEUP=", gave
    calls = (tmp_path / "cargo-calls.log").read_text().splitlines()
    assert len(calls) == {2: 3, 99: 1 if message == CARGO_COMPILE else 8}[fails], calls


def test_install_ps1_wires_the_retries_like_install_sh() -> None:
    ps1 = PS1.read_text(encoding="utf-8")
    assert "Invoke-Native -Description \"install Python $AfPython\" -Argv @($uv, 'python', 'install', $AfPython) -Retry uv" in ps1
    assert "$built = Invoke-Native -Description \"build $What\" -Argv $argv -Soft -Retry cargo" in ps1
    assert 'RUN_INDEX_RETRY=1 run "install Python $AF_PYTHON"' in TEXT
    assert 'RUN_SOFT=1 RUN_INDEX_RETRY=cargo run "build $_bc_what"' in TEXT
    # Same strings in both installers.
    for sh_name, ps_name in [("AF_UV_DETERMINISTIC", "UvDeterministic"), ("AF_UV_TRANSIENT", "UvTransient"), ("AF_CARGO_LAG", "CargoLag"),
                             ("AF_CARGO_DETERMINISTIC", "CargoDeterministic"), ("AF_CARGO_TRANSIENT", "CargoTransient")]:
        sh_val = re.search(rf"^{sh_name}='([^']*)'", TEXT, re.M).group(1)
        ps_val = re.search(rf"^\$script:{ps_name} = '([^']*)'", ps1, re.M).group(1)
        assert sh_val == ps_val, sh_name
