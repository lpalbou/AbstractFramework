"""The installers bring every browser app the gateway installed to the release's version.

install.sh's `# >>> apps-upgrade` block and install.ps1's Get-AppPin / Get-AppsInstalled /
Write-AppsMarker / Invoke-AppsStep run against a fake `abstractgateway` that keeps its apps in a
JSON file: an outdated app is updated through `abstractgateway apps update <id> --version <pin>`
(the gateway owns the install), an app at the pin is left alone, a failed update is reported in
the incomplete list (never silent), and with no gateway answering the pins go to
<data dir>/apps-upgrade.pending for the gateway's next start. Hermetic: no network, no keys.

Root backlog 1026 (a remote upgrade moved the gateway and left Flow where it was): the admin
token goes to `abstractgateway apps` as a parameter (the shell's ABSTRACTGATEWAY_AUTH_TOKEN, set
for another gateway, is not what the fake accepts), an app the gateway is still starting is
waited for, a copy running outside the gateway ("external") no longer hides the gateway's own
install (that is updated, and the summary says in red which copy runs), and a gateway whose
/api/health still says "starting" is not booted yet.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SH = ROOT / "scripts" / "install.sh"
PS1 = ROOT / "scripts" / "install.ps1"
PWSH = shutil.which("pwsh") or next(
    (str(p) for p in [ROOT / "untracked" / "root-0.6.2-gate" / "pwsh" / "pwsh"] if p.exists()), None
)

FAKE_GW = r"""#!/bin/sh
# fake `abstractgateway apps ...` over $FAKE_APPS (a JSON list of {id, version, running} rows; a row
# may carry source/status/managed_version/external like the gateway's). With FAKE_TOKEN set, a call
# must pass `--token $FAKE_TOKEN` (the environment's ABSTRACTGATEWAY_AUTH_TOKEN is not it); with
# FAKE_STARTING set, those apps are "starting" for the first $FAKE_STARTING_CALLS list calls.
[ "$1" = apps ] || exit 9
echo "$*" >>"$FAKE_CALLS"
if [ -n "$FAKE_TOKEN" ]; then case " $* " in *" --token $FAKE_TOKEN "*) ;; *) echo "error: Unauthorized" >&2; exit 1 ;; esac; fi
case "$2" in
  list) [ -n "$FAKE_LIST_FAIL" ] && exit 1
        "$FAKE_PY" - "$FAKE_APPS" "$FAKE_CALLS" <<'PY'
import json, os, sys
rows = json.load(open(sys.argv[1]))
n = sum(1 for line in open(sys.argv[2]) if line.split()[:2] == ["apps", "list"])
starting = os.environ.get("FAKE_STARTING", "").split()
if n <= int(os.environ.get("FAKE_STARTING_CALLS") or 0):
    for r in rows:
        if r["id"] in starting:
            r["status"] = "starting"
print(json.dumps({"apps": rows}))
PY
        ;;
  update) case " $FAKE_FAIL " in *" $3 "*) exit 1 ;; esac
        "$FAKE_PY" - "$FAKE_APPS" "$3" "$5" <<'PY'
import json, sys
p, app, ver = sys.argv[1:]
rows = json.load(open(p))
for r in rows:
    if r["id"] == app:
        # the gateway updates ITS install; a copy running outside it is not touched
        r["managed_version" if r.get("source") == "external" else "version"] = ver
json.dump(rows, open(p, "w"))
PY
        ;;
  *) exit 9 ;;
esac
"""

PINS = ("@abstractframework/flow@0.7.0 @abstractframework/code@0.10.0 @abstractframework/observer@0.6.0 "
        "@abstractframework/continuum@0.6.0 @abstractframework/entity@0.6.0")
INSTALLED = [
    {"id": "code", "version": "0.9.0", "running": True},
    {"id": "flow", "version": "0.7.0", "running": False},
    {"id": "entity", "version": "0.5.2", "running": False},
    {"id": "observer", "version": None, "running": False},
    {"id": "assistant", "version": "0.12.0", "running": False},
]


def _env(tmp_path: Path, apps: list, **extra: str) -> dict:
    gw = tmp_path / "abstractgateway"
    gw.write_text(FAKE_GW)
    gw.chmod(0o755)
    (tmp_path / "apps.json").write_text(json.dumps(apps))
    env = {k: v for k, v in os.environ.items() if not k.upper().endswith(("_KEY", "_TOKEN"))}
    env.update({"HOME": str(tmp_path), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "NO_COLOR": "1",
                "FAKE_APPS": str(tmp_path / "apps.json"), "FAKE_CALLS": str(tmp_path / "calls"),
                "FAKE_PY": sys.executable})
    env.update(extra)
    return env


def _calls(tmp_path: Path) -> list:
    f = tmp_path / "calls"
    return [c for c in f.read_text().splitlines() if " update " in f" {c} "] if f.exists() else []


def _versions(tmp_path: Path) -> dict:
    return {r["id"]: r["version"] for r in json.loads((tmp_path / "apps.json").read_text())}


def _rows(tmp_path: Path) -> dict:
    return {r["id"]: r for r in json.loads((tmp_path / "apps.json").read_text())}


def _list_calls(tmp_path: Path) -> int:
    f = tmp_path / "calls"
    return sum(1 for c in f.read_text().splitlines() if c.startswith("apps list")) if f.exists() else 0


def _token_file(tmp_path: Path, token: str) -> None:
    (tmp_path / "data" / "auth").mkdir(parents=True)
    (tmp_path / "data" / "auth" / "bootstrap-admin-token").write_text(token + "\n")


EXTERNAL = [
    # Flow: the gateway installed 0.6.0, but a copy started outside it (older) holds the port.
    {"id": "flow", "version": "0.6.0", "running": True, "source": "external", "status": "running", "managed_version": "0.6.0",
     "external": {"version": "0.6.0", "port": 3005, "pid": 4242}},
    # Code: the gateway installed nothing; only an outside copy runs, already at the pin.
    {"id": "code", "version": "0.10.0", "running": True, "source": "external", "status": "running", "managed_version": None,
     "external": {"version": "0.10.0", "port": 3003, "pid": 4343}},
    {"id": "entity", "version": "0.5.2", "running": False, "source": "gateway", "status": "stopped"},
]


def _sh(tmp_path: Path, env: dict, up: int, print_mode: int = 0) -> str:
    text = SH.read_text()
    block = re.search(r"^# >>> apps-upgrade.*?^# <<< apps-upgrade$", text, re.S | re.M)
    assert block, "install.sh lost its apps-upgrade block"
    script = f"""
info() {{ echo "INFO $1"; }}; ok() {{ echo "OK $1"; }}; warn() {{ echo "WARN $1"; }}
show_cmd() {{ echo "$*"; }}
run() {{ shift; RUN_RC=0; "$@" >/dev/null 2>&1 || RUN_RC=$?; return 0; }}
INCOMPLETE=""; incomplete_add() {{ INCOMPLETE="${{INCOMPLETE}}$1: $2
"; }}
AF_NPM_APPS="{PINS}"; GW="{tmp_path}/abstractgateway"; APPS_PY="{sys.executable}"
BASE_URL="http://127.0.0.1:18999"; DATA_DIR="{tmp_path}/data"; LOG_FILE=""; PRINT={print_mode}
AF_APPS_START_WAIT=6
{block.group(0)}
af_apps_step {up}
printf 'APPS<<%s>>\\nINCOMPLETE<<%s>>\\n' "$APPS_LINES" "$INCOMPLETE"
"""
    proc = subprocess.run(["sh", "-c", script], capture_output=True, text=True, env=env, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout + proc.stderr


def _ps(tmp_path: Path, env: dict, up: int, print_mode: int = 0) -> str:
    names = ["Get-AppPin", "Test-GwBooted", "Get-AppsToken", "Get-AppsInstalled", "Get-AppsSettled", "Write-AppsMarker", "Invoke-AppsStep"]
    loader = f"""
$ast = [System.Management.Automation.Language.Parser]::ParseFile('{PS1}', [ref]$null, [ref]$null)
$names = @({", ".join(repr(n) for n in names)})
$found = @($ast.FindAll({{ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $names -contains $n.Name }}, $true))
if ($found.Count -ne $names.Count) {{ throw "install.ps1 lost an apps-upgrade function" }}
$script:AppsStartWait = 6
foreach ($f in $found) {{ Invoke-Expression $f.Extent.Text }}
# Write-Host, like the installer's own: a message must never join a function's return value.
function Write-Info([string]$Text) {{ Write-Host "INFO $Text" }}
function Write-Ok([string]$Text) {{ Write-Host "OK $Text" }}
function Write-Warn2([string]$Text) {{ Write-Host "WARN $Text" }}
$script:Incomplete = New-Object System.Collections.Generic.List[string]
function Add-Incomplete([string]$Label, [string]$Why, [switch]$Fail) {{ $script:Incomplete.Add("${{Label}}: $Why") }}
$script:Twins = New-Object System.Collections.Generic.List[string]
$script:DryRun = ${'true' if print_mode else 'false'}
$AfNpmApps = @({", ".join(repr(s) for s in PINS.split())})
Invoke-AppsStep -Up ${'true' if up else 'false'} -Gw '{tmp_path}/abstractgateway' -BaseUrl 'http://127.0.0.1:18999' -DataDir '{tmp_path}/data'
"APPS<<$($script:AppsLines -join "`n")>>"
"INCOMPLETE<<$($script:Incomplete -join "`n")>>"
"""
    proc = subprocess.run([PWSH, "-NoProfile", "-Command", loader], capture_output=True, text=True, env=env, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout + proc.stderr


RUNNERS = [pytest.param(_sh, id="install.sh"),
           pytest.param(_ps, id="install.ps1", marks=pytest.mark.skipif(PWSH is None, reason="needs pwsh"))]


@pytest.mark.parametrize("runner", RUNNERS)
def test_outdated_apps_are_updated_through_the_gateway(runner, tmp_path: Path) -> None:
    out = runner(tmp_path, _env(tmp_path, INSTALLED), up=1)
    calls = _calls(tmp_path)
    assert any(c.startswith("apps update code --version 0.10.0") for c in calls), calls
    assert any(c.startswith("apps update entity --version 0.6.0") for c in calls), calls
    assert not any(" flow " in f" {c} " or " observer " in f" {c} " or " assistant " in f" {c} " for c in calls), calls
    v = _versions(tmp_path)
    assert (v["code"], v["entity"], v["flow"], v["observer"]) == ("0.10.0", "0.6.0", "0.7.0", None)
    assert "code 0.9.0 -> 0.10.0" in out and "entity 0.5.2 -> 0.6.0" in out and "flow 0.7.0" in out
    assert "INCOMPLETE<<>>" in out


@pytest.mark.parametrize("runner", RUNNERS)
def test_a_failed_update_is_loud(runner, tmp_path: Path) -> None:
    out = runner(tmp_path, _env(tmp_path, INSTALLED, FAKE_FAIL="code"), up=1)
    assert "code 0.9.0 (NOT 0.10.0" in out
    inc = out.split("INCOMPLETE<<", 1)[1]
    assert "code" in inc and "0.10.0" in inc


@pytest.mark.parametrize("runner", RUNNERS)
def test_an_unreadable_app_list_is_loud(runner, tmp_path: Path) -> None:
    out = runner(tmp_path, _env(tmp_path, INSTALLED, FAKE_LIST_FAIL="1"), up=1)
    assert "browser apps" in out.split("INCOMPLETE<<", 1)[1]


@pytest.mark.parametrize("runner", RUNNERS)
def test_print_plans_without_changing(runner, tmp_path: Path) -> None:
    out = runner(tmp_path, _env(tmp_path, INSTALLED), up=1, print_mode=1)
    assert _calls(tmp_path) == []
    assert "would update code 0.9.0 -> 0.10.0" in out and "would update entity 0.5.2 -> 0.6.0" in out


@pytest.mark.parametrize("runner", RUNNERS)
def test_no_gateway_writes_the_pending_marker(runner, tmp_path: Path) -> None:
    out = runner(tmp_path, _env(tmp_path, INSTALLED), up=0)
    marker = tmp_path / "data" / "apps-upgrade.pending"
    assert marker.read_text().split("\n")[:2] == ["flow 0.7.0", "code 0.10.0"]
    assert _calls(tmp_path) == [] and "next start" in out


@pytest.mark.parametrize("runner", RUNNERS)
def test_the_admin_token_is_passed_as_a_parameter(runner, tmp_path: Path) -> None:
    # The shell's ABSTRACTGATEWAY_AUTH_TOKEN belongs to another gateway (or is stale); the fake
    # answers Unauthorized to anything but the data dir's token, given as --token.
    _token_file(tmp_path, "the-data-dirs-token")
    out = runner(tmp_path, _env(tmp_path, INSTALLED, FAKE_TOKEN="the-data-dirs-token", ABSTRACTGATEWAY_AUTH_TOKEN="stale"), up=1)
    assert _versions(tmp_path)["code"] == "0.10.0" and "code 0.9.0 -> 0.10.0" in out
    assert "INCOMPLETE<<>>" in out


@pytest.mark.parametrize("runner", RUNNERS)
def test_without_the_token_the_refusal_is_loud(runner, tmp_path: Path) -> None:
    out = runner(tmp_path, _env(tmp_path, INSTALLED, FAKE_TOKEN="the-data-dirs-token"), up=1)
    assert _versions(tmp_path)["code"] == "0.9.0" and _calls(tmp_path) == []
    assert "browser apps" in out.split("INCOMPLETE<<", 1)[1]


@pytest.mark.parametrize("runner", RUNNERS)
def test_an_app_the_gateway_is_still_starting_is_waited_for(runner, tmp_path: Path) -> None:
    out = runner(tmp_path, _env(tmp_path, INSTALLED, FAKE_STARTING="code", FAKE_STARTING_CALLS="2"), up=1)
    assert _list_calls(tmp_path) >= 3, "the step read the list again until code had started"
    assert "still starting code" in out and "code 0.9.0 -> 0.10.0" in out
    assert len([c for c in _calls(tmp_path) if " code " in f" {c} "]) == 1


@pytest.mark.parametrize("runner", RUNNERS)
def test_an_app_that_never_finishes_starting_is_updated_anyway(runner, tmp_path: Path) -> None:
    out = runner(tmp_path, _env(tmp_path, INSTALLED, FAKE_STARTING="code", FAKE_STARTING_CALLS="99"), up=1)
    assert "still starting after 6 s" in out and "code 0.9.0 -> 0.10.0" in out


@pytest.mark.parametrize("runner", RUNNERS)
def test_an_outside_copy_does_not_hide_the_gateways_install(runner, tmp_path: Path) -> None:
    out = runner(tmp_path, _env(tmp_path, EXTERNAL), up=1)
    calls = _calls(tmp_path)
    assert any(c.startswith("apps update flow --version 0.7.0") for c in calls), calls
    assert any(c.startswith("apps update entity --version 0.6.0") for c in calls), calls
    assert not any(" code " in f" {c} " for c in calls), "nothing installed by the gateway: nothing to update"
    rows = _rows(tmp_path)
    assert rows["flow"]["managed_version"] == "0.7.0" and rows["flow"]["version"] == "0.6.0", "the outside copy is not the gateway's to restart"
    apps = out.split("APPS<<", 1)[1].split(">>", 1)[0]
    assert "flow 0.6.0 -> 0.7.0; RUNNING: a copy started outside the gateway, 0.6.0 on port 3005 (pid 4242)" in apps
    assert "code: not installed by the gateway; a copy started outside it runs on port 3003 (0.10.0)" in apps
    inc = out.split("INCOMPLETE<<", 1)[1]
    assert "the flow app" in inc and "4242" in inc and "apps launch flow" in inc, inc
    assert "the code app" not in inc, "an outside copy at the pin is a note, not a failure"


def test_gw_booted_refuses_a_gateway_still_starting() -> None:
    text = SH.read_text()
    block = re.search(r"^# >>> apps-upgrade.*?^# <<< apps-upgrade$", text, re.S | re.M).group(0)
    script = block + """
for body in '{"status":"healthy","service":"abstractgateway"}' '{"status": "degraded", "service": "abstractgateway"}' \\
            '{"status": "starting", "service": "abstractgateway", "boot": {}}' '{"status":"starting","service":"abstractgateway"}' 'not a gateway' ''; do
    if gw_booted "$body"; then echo "BOOTED $body"; else echo "NOT $body"; fi
done
"""
    env = {"PATH": "/usr/bin:/bin", "NO_COLOR": "1"}
    out = subprocess.run(["sh", "-c", script], capture_output=True, text=True, env=env, timeout=30).stdout.splitlines()
    assert [line.split(" ", 1)[0] for line in out] == ["BOOTED", "BOOTED", "NOT", "NOT", "NOT", "NOT"], out


@pytest.mark.skipif(PWSH is None, reason="needs pwsh")
def test_ps1_gw_booted_refuses_a_gateway_still_starting() -> None:
    loader = f"""
$ast = [System.Management.Automation.Language.Parser]::ParseFile('{PS1}', [ref]$null, [ref]$null)
$f = @($ast.FindAll({{ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Test-GwBooted' }}, $true))
if ($f.Count -ne 1) {{ throw "install.ps1 lost Test-GwBooted" }}
Invoke-Expression $f[0].Extent.Text
foreach ($b in @('{{"status":"healthy","service":"abstractgateway"}}', '{{"status": "degraded", "service": "abstractgateway"}}',
                 '{{"status": "starting", "service": "abstractgateway"}}', '{{"status":"starting","service":"abstractgateway"}}', 'not a gateway', '')) {{
    if (Test-GwBooted $b) {{ "BOOTED" }} else {{ "NOT" }}
}}
"""
    proc = subprocess.run([PWSH, "-NoProfile", "-Command", loader], capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.split() == ["BOOTED", "BOOTED", "NOT", "NOT", "NOT", "NOT"], proc.stdout
