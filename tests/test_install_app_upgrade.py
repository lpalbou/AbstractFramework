"""The installers bring every browser app the gateway installed to the release's version.

install.sh's `# >>> apps-upgrade` block and install.ps1's Get-AppPin / Get-AppsInstalled /
Write-AppsMarker / Invoke-AppsStep run against a fake `abstractgateway` that keeps its apps in a
JSON file: an outdated app is updated through `abstractgateway apps update <id> --version <pin>`
(the gateway owns the install), an app at the pin is left alone, a failed update is reported in
the incomplete list (never silent), and with no gateway answering the pins go to
<data dir>/apps-upgrade.pending for the gateway's next start. Hermetic: no network, no keys.
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
# fake `abstractgateway apps ...` over $FAKE_APPS (a JSON list of {id, version, running})
[ "$1" = apps ] || exit 9
echo "$*" >>"$FAKE_CALLS"
case "$2" in
  list) [ -n "$FAKE_LIST_FAIL" ] && exit 1
        "$FAKE_PY" -c 'import json,sys; print(json.dumps({"apps": json.load(open(sys.argv[1]))}))' "$FAKE_APPS" ;;
  update) case " $FAKE_FAIL " in *" $3 "*) exit 1 ;; esac
        "$FAKE_PY" - "$FAKE_APPS" "$3" "$5" <<'PY'
import json, sys
p, app, ver = sys.argv[1:]
rows = json.load(open(p))
for r in rows:
    if r["id"] == app:
        r["version"] = ver
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
{block.group(0)}
af_apps_step {up}
printf 'APPS<<%s>>\\nINCOMPLETE<<%s>>\\n' "$APPS_LINES" "$INCOMPLETE"
"""
    proc = subprocess.run(["sh", "-c", script], capture_output=True, text=True, env=env, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout


def _ps(tmp_path: Path, env: dict, up: int, print_mode: int = 0) -> str:
    names = ["Get-AppPin", "Get-AppsInstalled", "Write-AppsMarker", "Invoke-AppsStep"]
    loader = f"""
$ast = [System.Management.Automation.Language.Parser]::ParseFile('{PS1}', [ref]$null, [ref]$null)
$names = @({", ".join(repr(n) for n in names)})
$found = @($ast.FindAll({{ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $names -contains $n.Name }}, $true))
if ($found.Count -ne $names.Count) {{ throw "install.ps1 lost an apps-upgrade function" }}
foreach ($f in $found) {{ Invoke-Expression $f.Extent.Text }}
function Write-Info([string]$Text) {{ Write-Output "INFO $Text" }}
function Write-Ok([string]$Text) {{ Write-Output "OK $Text" }}
function Write-Warn2([string]$Text) {{ Write-Output "WARN $Text" }}
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
    return proc.stdout


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
