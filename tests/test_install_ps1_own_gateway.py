"""install.ps1: a re-run finds this install's gateway started by hand, and uv revalidates its pins
(root backlog 0987, rehearsal 0.6.3 item 20 and the stale-index failure after the 0.7.4 release).

No Windows is needed: the installer's functions are loaded from the script's AST (running the script
would install) and the Windows-only probes (Get-NetTCPConnection, Win32_Process, Get-Process) are
replaced by fakes defined after them, so Find-OwnGateway sees exactly the listener, command line and
liveness each case gives. The serve record, the data-dir comparison and the decision are the real
code. Needs PowerShell 7 (`pwsh`); skipped without it. install.sh's twin of this logic runs against
real processes in scripts/tests/test_install_user_path.sh (section [21]).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install.ps1"
SH = ROOT / "scripts" / "install.sh"

needs_pwsh = pytest.mark.skipif(shutil.which("pwsh") is None, reason="needs PowerShell 7 (pwsh)")

REAL = ["Read-ServeRecord", "Test-CommandLineDataDir", "Find-OwnGateway", "Resolve-DirPath", "Get-RefreshPackages"]


def _pwsh(body: str, tmp_path: Path) -> str:
    script = str(SCRIPT).replace("'", "''")
    names = ", ".join(f"'{n}'" for n in REAL)
    loader = f"""
$ast = [System.Management.Automation.Language.Parser]::ParseFile('{script}', [ref]$null, [ref]$null)
$names = @({names})
foreach ($f in $ast.FindAll({{ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $names -contains $n.Name }}, $true)) {{ Invoke-Expression $f.Extent.Text }}
foreach ($a in $ast.EndBlock.Statements) {{
    if ($a -is [System.Management.Automation.Language.AssignmentStatementAst] -and $a.Left -is [System.Management.Automation.Language.VariableExpressionAst] -and $a.Left.VariablePath.UserPath -eq 'AfPyMatrix') {{ Invoke-Expression $a.Extent.Text }}
}}
"""
    env = {k: v for k, v in os.environ.items() if not k.upper().endswith(("_KEY", "_TOKEN"))}
    env.update({"HOME": str(tmp_path), "TERM": "dumb", "NO_COLOR": "1"})
    proc = subprocess.run(["pwsh", "-NoProfile", "-Command", loader + body], capture_output=True, text=True,
                          env=env, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout.strip()


def _ps(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _find(tmp_path: Path, *, listener: int, cmdline: str, alive: bool = True, health: bool = True,
          record: dict | None = None, port: int = 8080) -> int:
    data = tmp_path / "App Data" / "AbstractGateway"
    (data / "run").mkdir(parents=True, exist_ok=True)
    rec = data / "run" / "gateway-serve.json"
    if record is not None:
        rec.write_text(json.dumps({k: (str(data) if v == "SELF" else v) for k, v in record.items()}), encoding="utf-8")
    elif rec.exists():
        rec.unlink()
    body = f"""
function Get-PortListenerPid([int]$Port) {{ return {listener} }}
function Get-ProcessCommandLine([int]$ProcessId) {{ return {_ps(cmdline.replace('DATA', str(data)))} }}
function Test-ProcessAlive([int]$ProcessId) {{ return ${'true' if alive else 'false'} }}
function Get-Http([string]$Url) {{ if (${'true' if health else 'false'} -and $Url -eq 'http://127.0.0.1:{port}/api/health') {{ return '{{"status": "healthy", "service": "abstractgateway"}}' }}; return $null }}
Find-OwnGateway {port} {_ps(str(data))}
"""
    return int(_pwsh(body, tmp_path).splitlines()[-1])


GW = r"C:\Users\x\.local\bin\abstractgateway.exe serve --host 127.0.0.1 --port 8080"


@needs_pwsh
def test_the_serve_record_naming_the_listener_makes_it_ours(tmp_path: Path) -> None:
    assert _find(tmp_path, listener=4242, cmdline=GW, record={"pid": 4242, "port": 8080, "data_dir": "SELF"}) == 4242


@needs_pwsh
def test_the_command_line_data_dir_makes_it_ours_without_a_record(tmp_path: Path) -> None:
    # The data dir has a space: quoted on the command line, as Windows passes it.
    assert _find(tmp_path, listener=4242, cmdline=GW + ' --data-dir "DATA"') == 4242
    assert _find(tmp_path, listener=4242, cmdline=GW + ' "--data-dir=DATA"') == 4242


@needs_pwsh
def test_a_gateway_of_another_data_dir_is_foreign(tmp_path: Path) -> None:
    assert _find(tmp_path, listener=4242, cmdline=GW + r' --data-dir "C:\elsewhere\gw"') == 0
    # a record here names another pid (the listener is some other gateway)
    assert _find(tmp_path, listener=4242, cmdline=GW, record={"pid": 777, "port": 8080, "data_dir": "SELF"}) == 0
    # a record here naming the listener but another data dir (a copied folder)
    assert _find(tmp_path, listener=4242, cmdline=GW, record={"pid": 4242, "port": 8080, "data_dir": r"C:\elsewhere\gw"}) == 0


@needs_pwsh
def test_another_program_is_foreign_even_with_a_record_naming_it(tmp_path: Path) -> None:
    # a reused pid: the record names it, but it does not run abstractgateway
    assert _find(tmp_path, listener=4242, cmdline="python -m http.server 8080",
                 record={"pid": 4242, "port": 8080, "data_dir": "SELF"}) == 0
    assert _find(tmp_path, listener=4242, cmdline=GW, alive=False,
                 record={"pid": 4242, "port": 8080, "data_dir": "SELF"}) == 0


@needs_pwsh
def test_without_a_named_listener_the_record_and_health_decide(tmp_path: Path) -> None:
    rec = {"pid": 4242, "port": 8080, "data_dir": "SELF"}
    assert _find(tmp_path, listener=0, cmdline=GW, record=rec) == 4242
    assert _find(tmp_path, listener=0, cmdline=GW, record=rec, health=False) == 0
    assert _find(tmp_path, listener=0, cmdline=GW, record={**rec, "port": 8081}) == 0
    assert _find(tmp_path, listener=0, cmdline=GW, record=None) == 0


@needs_pwsh
def test_refresh_packages_are_the_gateway_and_the_release_matrix_in_both_installers(tmp_path: Path) -> None:
    ps = _pwsh("(Get-RefreshPackages) -join ' '", tmp_path).split()
    sh = SH.read_text(encoding="utf-8")
    matrix = re.search(r'^AF_PY_MATRIX="([^"]+)"$', sh, flags=re.M)
    assert matrix
    names = [c.split("==")[0] for c in matrix.group(1).split()]
    assert ps == ["abstractgateway", *names]
    out = subprocess.run(["sh", "-c", f'. /dev/stdin <<"EOF"\n{_sh_function(sh, "af_refresh_packages")}\nAF_PY_MATRIX="{matrix.group(1)}"\naf_refresh_packages\nEOF'],
                         check=True, capture_output=True, text=True).stdout.split()
    assert out == ps


def _sh_function(text: str, name: str) -> str:
    m = re.search(rf"^{name}\(\) \{{\n.*?^\}}$", text, flags=re.M | re.S)
    assert m, name
    return m.group(0)


def test_install_ps1_wires_the_own_gateway_check_and_the_refresh() -> None:
    ps1 = SCRIPT.read_text(encoding="utf-8")
    port = ps1[ps1.index("    if (Test-PortBusy $Port) {"):ps1.index("    $baseUrl = \"http://127.0.0.1:$Port\"")]
    # recognised before the -NoStart hold, the explicit-port refusal and the move to the next port
    order = [port.index(s) for s in ("if ($ours)", "Find-OwnGateway $Port $DataDir", "elseif ($NoStart", "elseif ($explicitPort)", "using $p (kept for future runs)")]
    assert order == sorted(order)
    # the gateway.pid process counts only when it is the listener
    assert "(-not $listener -or $listener -eq $ourPid)" in port
    # the hand-started gateway is among the gateways stopped before the installer's start
    running = ps1[ps1.index("function Get-RunningGatewayPids"):ps1.index("function Stop-RunningGateway")]
    assert "$script:HandGatewayPid" in running
    install = ps1[ps1.index("function Install-Gateway("):ps1.index("function Install-GatewayVoice(")]
    assert "foreach ($p in (Get-RefreshPackages)) { $argv += @('--refresh-package', $p) }" in install
    assert "'--refresh'" not in install


@needs_pwsh
def test_install_ps1_print_refreshes_the_pins_and_starts_with_launch_flags(tmp_path: Path) -> None:
    env = {**os.environ, "HOME": str(tmp_path), "USERPROFILE": str(tmp_path), "LOCALAPPDATA": str(tmp_path / "lad"),
           "PROCESSOR_ARCHITECTURE": "AMD64"}
    env["PATH"] = os.pathsep.join([os.path.dirname(shutil.which("pwsh")), "/usr/bin", "/bin"])
    argv = ["pwsh", "-NoProfile", "-File", str(SCRIPT), "-Print", "-Profile", "light", "-Port", "18999", "-NoService"]
    out = subprocess.run(argv, check=True, capture_output=True, text=True, env=env).stdout
    install = next(line for line in out.splitlines() if " tool install " in line)
    for name in ["abstractgateway", *[c.split("==")[0] for c in re.findall(r"'([^']+==[^']+)'", re.search(r"^\$AfPyMatrix = @\((.*)\)$", SCRIPT.read_text(), flags=re.M).group(1))]]:
        assert f" --refresh-package {name} " in install + " ", name
    start = next(line for line in out.splitlines() if "Start-Process -FilePath" in line and "serve" in line)
    # -Print cannot ask the Network setting, so it shows the pinned bind; the data dir is a launch flag.
    assert "-ArgumentList 'serve --host 127.0.0.1 --port 18999 --data-dir " in start
    assert "ABSTRACTGATEWAY_" not in start
    assert not (tmp_path / "lad").exists(), "-Print must not write anything"
