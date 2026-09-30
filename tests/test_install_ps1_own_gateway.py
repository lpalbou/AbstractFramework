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

REAL = ["Read-ServeRecord", "Test-CommandLineDataDir", "Get-DeclaredDataDir", "Test-OwnGatewayPid", "Find-OwnGateway",
        "Test-OurBackgroundListener", "Test-RecordNamesThisGateway", "Resolve-DirPath", "Get-RefreshPackages",
        "Test-SameUser", "Test-GatewayCommandLine", "Test-PidFileGateway", "Test-GatewayPidStillOurs"]
STARTED = "2026-09-30T10:00:00Z"          # when the fake process started (UTC)
WRITTEN = "2026-09-30T10:00:05.123456Z"   # the serve record's started_at, as the gateway writes it


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
          record: dict | None = None, port: int = 8080, started: str = STARTED, in_parent: bool = False,
          owner: str = "SAME") -> int:
    data = tmp_path / "App Data" / "AbstractGateway"
    (data / "run").mkdir(parents=True, exist_ok=True)
    rec = data / "run" / "gateway-serve.json"
    if record is not None:
        rec.write_text(json.dumps({"started_at": WRITTEN, **{k: (str(data) if v == "SELF" else v) for k, v in record.items()}}), encoding="utf-8")
    elif rec.exists():
        rec.unlink()
    body = f"""
function Get-PortListenerPid([int]$Port) {{ return {listener} }}
function Get-ProcessCommandLine([int]$ProcessId) {{ return {_ps(cmdline.replace('DATA', str(data)))} }}
function Test-ProcessAlive([int]$ProcessId) {{ return ${'true' if alive else 'false'} }}
function Get-ProcessOwner([int]$ProcessId) {{ if ({_ps(owner)} -eq 'SAME') {{ return [Environment]::UserName }}; return {_ps(owner)} }}
function Get-ProcessStartUtc([int]$ProcessId) {{ return [DateTime]::Parse('{started}', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AdjustToUniversal) }}
function Get-Http([string]$Url) {{ if (${'true' if health else 'false'} -and $Url -eq 'http://127.0.0.1:{port}/api/health') {{ return '{{"status": "healthy", "service": "abstractgateway"}}' }}; return $null }}
{'Set-Location ' + _ps(str(data.parent)) if in_parent else ''}
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
    order = [port.index(s) for s in ("if ($ours)", "elseif (($script:HandGatewayPid = Find-OwnGateway $Port $DataDir))", "elseif ($NoStart", "elseif ($explicitPort)", "using $p (kept for future runs)")]
    assert order == sorted(order)
    # the gateway.pid process counts only when it (or its child: uv's launcher runs python.exe) is the listener
    assert "Test-OurBackgroundListener $listener ([int]$ourPid)" in port
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


@needs_pwsh
def test_the_gate_repros_are_foreign(tmp_path: Path) -> None:
    rec = {"pid": 4242, "port": 8080, "data_dir": "SELF"}
    # a gateway whose own --data-dir is another one, although the record here names it
    assert _find(tmp_path, listener=4242, cmdline=GW + ' --data-dir "/elsewhere/gw"', record=rec) == 0
    # a relative --data-dir this installer cannot resolve (no working directory of another process on Windows)
    assert _find(tmp_path, listener=4242, cmdline=GW + " --data-dir AbstractGateway", record=rec) == 0
    # ... even when the installer itself runs in the folder that would make it this data dir
    assert _find(tmp_path, listener=4242, cmdline=GW + " --data-dir AbstractGateway", record=rec, in_parent=True) == 0
    # a stale record: the process started after the record was written (a reused pid)
    assert _find(tmp_path, listener=4242, cmdline=GW, record=rec, started="2026-09-30T11:00:00Z") == 0
    # a program that mentions abstractgateway but does not run `abstractgateway serve`
    assert _find(tmp_path, listener=4242, cmdline=r"tail -f C:\x\abstractgateway-logs\x", record=rec) == 0
    # the listener named, but /api/health there is not a gateway's
    assert _find(tmp_path, listener=4242, cmdline=GW, record=rec, health=False) == 0
    # a gateway of another user (its owner is not the user running the installer)
    assert _find(tmp_path, listener=4242, cmdline=GW, record=rec, owner="someoneelse") == 0
    # the owner cannot be told: not ours
    assert _find(tmp_path, listener=4242, cmdline=GW, record=rec, owner="") == 0


@needs_pwsh
def test_the_installers_background_gateway_is_its_launcher_or_the_launchers_child(tmp_path: Path) -> None:
    # uv's abstractgateway.exe (gateway.pid = 100) runs python.exe (pid 101), the listener.
    body = """
function Get-ParentProcessId([int]$ProcessId) { if ($ProcessId -eq 101) { return 100 }; return 1 }
@((Test-OurBackgroundListener 101 100), (Test-OurBackgroundListener 100 100), (Test-OurBackgroundListener 0 100),
  (Test-OurBackgroundListener 555 100), (Test-OurBackgroundListener 101 0)) -join ' '
"""
    assert _pwsh(body, tmp_path).splitlines()[-1] == "True True True False False"


@needs_pwsh
def test_a_stale_record_never_adds_a_reused_pid_to_the_gateways_stopped(tmp_path: Path) -> None:
    data = tmp_path / "gw"
    def names(cmd: str, started: str) -> str:
        body = f"""
function Test-ProcessAlive([int]$ProcessId) {{ return $true }}
function Get-ProcessOwner([int]$ProcessId) {{ return [Environment]::UserName }}
function Get-ProcessCommandLine([int]$ProcessId) {{ return {_ps(cmd)} }}
function Get-ProcessStartUtc([int]$ProcessId) {{ return [DateTime]::Parse('{started}', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AdjustToUniversal) }}
Test-RecordNamesThisGateway ([pscustomobject]@{{ pid = 4242; port = 8080; data_dir = {_ps(str(data))}; started_at = '{WRITTEN}' }}) {_ps(str(data))}
"""
        return _pwsh(body, tmp_path).splitlines()[-1]
    assert names(GW, STARTED) == "True"
    assert names(GW, "2026-09-30T11:00:00Z") == "False"
    assert names(r"tail -f C:\x\abstractgateway-logs\x", STARTED) == "False"
    assert names(GW + ' --data-dir "/elsewhere/gw"', STARTED) == "False"



def _pidfile_case(tmp_path: Path, *, named: int, pid: int, cmd: str, started: str, owner: str = "SAME",
                  record: dict | None = None, hand: int = 0, own_found: int = 0, fn: str = "Test-PidFileGateway") -> str:
    data = tmp_path / "gw"
    (data / "run").mkdir(parents=True, exist_ok=True)
    pidfile = data / "gateway.pid"
    pidfile.write_text(f"{named}\n")
    os.utime(pidfile, (1790762405, 1790762405))  # 2026-09-30T10:00:05Z, when the installer wrote it
    rec = data / "run" / "gateway-serve.json"
    if record is not None:
        rec.write_text(json.dumps({"started_at": WRITTEN, "data_dir": str(data), **record}), encoding="utf-8")
    elif rec.exists():
        rec.unlink()
    call = (f"Test-PidFileGateway {pid} {_ps(str(pidfile))} {_ps(str(data))}" if fn == "Test-PidFileGateway"
            else f"Test-GatewayPidStillOurs {pid} {_ps(str(pidfile))} {_ps(str(data))} 8080 {hand}")
    body = f"""
function Test-ProcessAlive([int]$ProcessId) {{ return $true }}
function Get-ProcessOwner([int]$ProcessId) {{ if ({_ps(owner)} -eq 'SAME') {{ return [Environment]::UserName }}; return {_ps(owner)} }}
function Get-ProcessCommandLine([int]$ProcessId) {{ return {_ps(cmd.replace('DATA', str(data)))} }}
function Get-ProcessStartUtc([int]$ProcessId) {{ return [DateTime]::Parse('{started}', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AdjustToUniversal) }}
function Find-OwnGateway([int]$Port, [string]$DataDir) {{ return {own_found} }}
{call}
"""
    return _pwsh(body, tmp_path).splitlines()[-1]


LAUNCHER = r'"C:\Users\x\.local\bin\abstractgateway.exe" serve'


@needs_pwsh
def test_gateway_pid_is_trusted_only_for_this_installs_gateway(tmp_path: Path) -> None:
    # the installer's background gateway (uv's launcher), started before gateway.pid was written
    assert _pidfile_case(tmp_path, named=100, pid=100, cmd=LAUNCHER, started=STARTED) == "True"
    assert _pidfile_case(tmp_path, named=100, pid=100, cmd=LAUNCHER + ' --data-dir "DATA"', started=STARTED) == "True"
    # the gate's repro: gateway.pid names a foreign `sleep 120`
    assert _pidfile_case(tmp_path, named=100, pid=100, cmd="sleep 120", started=STARTED) == "False"
    # a gateway process that started after gateway.pid was written (the pid was reused)
    assert _pidfile_case(tmp_path, named=100, pid=100, cmd=LAUNCHER, started="2026-09-30T11:00:00Z") == "False"
    # ... unless the serve record names it (it wrote the record after it started)
    assert _pidfile_case(tmp_path, named=100, pid=100, cmd=LAUNCHER, started="2026-09-30T10:00:04Z",
                         record={"pid": 100, "port": 8080}) == "True"
    # a gateway of another data dir, of another user, or a pid the file does not name
    assert _pidfile_case(tmp_path, named=100, pid=100, cmd=LAUNCHER + ' --data-dir "/elsewhere/gw"', started=STARTED) == "False"
    assert _pidfile_case(tmp_path, named=100, pid=100, cmd=LAUNCHER, started=STARTED, owner="someoneelse") == "False"
    assert _pidfile_case(tmp_path, named=101, pid=100, cmd=LAUNCHER, started=STARTED) == "False"


@needs_pwsh
def test_every_stop_target_is_checked_again_right_before_stop_process(tmp_path: Path) -> None:
    kw = {"fn": "Test-GatewayPidStillOurs", "started": STARTED}
    # the hand-started gateway: only while Find-OwnGateway still finds that pid on the port
    assert _pidfile_case(tmp_path, named=100, pid=200, cmd=GW, hand=200, own_found=200, **kw) == "True"
    assert _pidfile_case(tmp_path, named=100, pid=200, cmd=GW, hand=200, own_found=0, **kw) == "False"
    # the pid-file gateway: only while it is still that gateway
    assert _pidfile_case(tmp_path, named=100, pid=100, cmd=LAUNCHER, **kw) == "True"
    assert _pidfile_case(tmp_path, named=100, pid=100, cmd="sleep 120", **kw) == "False"
    # the serve record's gateway (the login item): only while the record still names a gateway that predates it
    assert _pidfile_case(tmp_path, named=100, pid=300, cmd=GW, record={"pid": 300, "port": 8080}, **kw) == "True"
    assert _pidfile_case(tmp_path, named=100, pid=300, cmd="notepad.exe", record={"pid": 300, "port": 8080}, **kw) == "False"


def test_install_ps1_checks_every_pid_before_stopping_it() -> None:
    ps1 = SCRIPT.read_text(encoding="utf-8")
    stop = ps1[ps1.index("    function Stop-RunningGateway {"):ps1.index("    if (-not $script:DryRun) {\n        New-Item -ItemType Directory -Force -Path $logDir")]
    assert stop.index("Test-GatewayPidStillOurs $p $pidFile $DataDir $Port $script:HandGatewayPid") < stop.index("Stop-Process -Id $p -Force")
    our = ps1[ps1.index("    function Get-OurPid {"):ps1.index("    function Stop-OurGateway {")]
    assert "Test-PidFileGateway $p $pidFile $DataDir" in our
    port = ps1[ps1.index("    if (Test-PortBusy $Port) {"):ps1.index("    $baseUrl = \"http://127.0.0.1:$Port\"")]
    # the login item (service mode): a healthy gateway of THIS data dir, when the listener can be named
    assert "(-not $listener -or (Find-OwnGateway $Port $DataDir) -eq $listener)" in port
