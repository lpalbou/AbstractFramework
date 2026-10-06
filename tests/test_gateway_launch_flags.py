"""The gateway launchers pass the backlog settings as `serve` flags (root backlog 1002 item 5).

Gateway 0.13.0 takes the backlog folder and the backlog exec runner as
`serve --backlog-root PATH --exec-runner on|off` and no longer reads the
ABSTRACTGATEWAY_TRIAGE_REPO_ROOT / ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER variables (it imports a
leftover value once into the saved setting). scripts/lib/gateway_flags.sh builds the flags when
`abstractgateway --version` is 0.13.0 or newer; for an older gateway it exports the two variables
and prints one note. scripts/gateway.sh and scripts/gateway-local.sh take `--print` (show the
serve command, then exit before anything is stopped or created).

A fake python stands in for the real one: `-P -m abstractgateway --version` prints the version in
$FAKE_GATEWAY_VERSION (nothing and exit 1 when it is empty).
"""

from __future__ import annotations

import os
import shlex
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FLAGS_LIB = SCRIPTS / "lib" / "gateway_flags.sh"

FAKE_PY = """#!/bin/sh
if [ "$1" = "-P" ] && [ "$2" = "-m" ] && [ "$3" = "abstractgateway" ] && [ "$4" = "--version" ]; then
    [ -n "$FAKE_GATEWAY_VERSION" ] || exit 1
    echo "abstractgateway $FAKE_GATEWAY_VERSION"
    exit 0
fi
echo "fake python: unexpected call: $*" >&2
exit 3
"""


@pytest.fixture()
def sandbox(tmp_path: Path) -> dict:
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    py = venv_bin / "python"
    py.write_text(FAKE_PY, encoding="utf-8")
    py.chmod(py.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    home = tmp_path / "home"
    home.mkdir()
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "RUNTIME_DIR": str(tmp_path / "runtime"),
        "PYTHON_BIN": str(py),
        "AF_VENV_DIR": str(tmp_path / "venv"),
    }
    return {"tmp": tmp_path, "py": py, "env": env}


def _run(cmd: list[str], env: dict, **extra: str) -> subprocess.CompletedProcess:
    full = dict(env)
    full.update(extra)
    return subprocess.run(cmd, env=full, capture_output=True, text=True, timeout=60)


def _print(launcher: str, sandbox: dict, **extra: str) -> tuple[list[str], str]:
    res = _run(["bash", str(SCRIPTS / launcher), "--print"], sandbox["env"], **extra)
    assert res.returncode == 0, res.stderr
    return shlex.split(res.stdout), res.stderr


def _after_serve(argv: list[str]) -> list[str]:
    return argv[argv.index("serve") + 1 :]


@pytest.mark.parametrize("launcher", ["gateway.sh", "gateway-local.sh"])
@pytest.mark.parametrize("version", ["0.13.0", "0.13.1", "0.14.0", "1.0.0"])
def test_new_gateway_gets_flags_not_variables(sandbox, launcher, version):
    argv, err = _print(launcher, sandbox, FAKE_GATEWAY_VERSION=version)
    assert argv[0] == str(sandbox["py"])
    assert argv[1:4] == ["-P", "-m", "abstractgateway"]
    args = _after_serve(argv)
    assert args[args.index("--backlog-root") + 1] == str(ROOT)
    assert args[args.index("--exec-runner") + 1] == "on"
    assert "--host" in args and "--port" in args
    assert "note:" not in err


@pytest.mark.parametrize("launcher", ["gateway.sh", "gateway-local.sh"])
@pytest.mark.parametrize("version", ["0.12.0", "0.9.6", ""])
def test_old_or_unknown_gateway_keeps_variables_with_one_note(sandbox, launcher, version):
    argv, err = _print(launcher, sandbox, FAKE_GATEWAY_VERSION=version)
    args = _after_serve(argv)
    assert "--backlog-root" not in args and "--exec-runner" not in args
    notes = [line for line in err.splitlines() if line.startswith("note:")]
    assert len(notes) == 1 and "older than 0.13.0" in notes[0], err


def test_exec_runner_knob_off(sandbox):
    argv, _ = _print("gateway.sh", sandbox, FAKE_GATEWAY_VERSION="0.13.0", ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER="0")
    args = _after_serve(argv)
    assert args[args.index("--exec-runner") + 1] == "off"


def test_root_without_backlog_passes_no_backlog_root(sandbox):
    bare = sandbox["tmp"] / "bare"
    bare.mkdir()
    argv, err = _print("gateway.sh", sandbox, FAKE_GATEWAY_VERSION="0.13.0", ABSTRACTGATEWAY_TRIAGE_REPO_ROOT=str(bare))
    args = _after_serve(argv)
    assert "--backlog-root" not in args
    assert args[args.index("--exec-runner") + 1] == "on"
    assert "has no docs/backlog folder" in err


def _lib(sandbox: dict, body: str, **extra: str) -> subprocess.CompletedProcess:
    script = f"set -euo pipefail\nsource {shlex.quote(str(FLAGS_LIB))}\n{body}\n"
    return _run(["bash", "-c", script], sandbox["env"], **extra)


ENV_DUMP = 'gateway_backlog_flags "$PYTHON_BIN" "$ROOT" {default}\necho "FLAGS=${{GATEWAY_SERVE_FLAGS[*]:-}}"\nenv | grep "^ABSTRACTGATEWAY_" | sort || true'


def test_new_gateway_unsets_shell_variables_and_uses_their_value(sandbox):
    custom = sandbox["tmp"] / "custom"
    (custom / "docs" / "backlog").mkdir(parents=True)
    res = _lib(
        sandbox,
        ENV_DUMP.format(default=""),
        FAKE_GATEWAY_VERSION="0.13.0",
        ROOT=str(ROOT),
        ABSTRACTGATEWAY_TRIAGE_REPO_ROOT=str(custom),
        ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER="yes",
    )
    assert res.returncode == 0, res.stderr
    assert f"FLAGS=--backlog-root {custom} --exec-runner on" in res.stdout
    assert "ABSTRACTGATEWAY_" not in res.stdout.replace("FLAGS=", "")


def test_old_gateway_exports_the_variables(sandbox):
    res = _lib(sandbox, ENV_DUMP.format(default=""), FAKE_GATEWAY_VERSION="0.12.0", ROOT=str(ROOT))
    assert res.returncode == 0, res.stderr
    assert "FLAGS=\n" in res.stdout
    assert f"ABSTRACTGATEWAY_TRIAGE_REPO_ROOT={ROOT}" in res.stdout
    assert "ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER=1" in res.stdout


def test_empty_runner_default_passes_no_runner_choice(sandbox):
    """gateway-flow-local.sh never chose the exec runner: it still does not."""
    res = _lib(sandbox, ENV_DUMP.format(default='""'), FAKE_GATEWAY_VERSION="0.13.0", ROOT=str(ROOT))
    assert res.returncode == 0, res.stderr
    assert f"FLAGS=--backlog-root {ROOT}\n" in res.stdout
    res = _lib(sandbox, ENV_DUMP.format(default='""'), FAKE_GATEWAY_VERSION="0.12.0", ROOT=str(ROOT))
    assert "ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER" not in res.stdout


def test_sourcing_apps_common_exports_no_backlog_variable(sandbox):
    script = f"source {shlex.quote(str(SCRIPTS / 'lib' / 'apps_common.sh'))}\nenv | grep -E '^ABSTRACTGATEWAY_(TRIAGE|BACKLOG)' || echo NONE"
    res = _run(["bash", "-c", script], sandbox["env"])
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == "NONE"


def test_no_launcher_exports_the_backlog_variables():
    offenders = []
    for path in sorted(SCRIPTS.rglob("*.sh")):
        if "tests" in path.relative_to(SCRIPTS).parts or path == FLAGS_LIB:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("#", 1)[0]
            if "export" in code and ("ABSTRACTGATEWAY_TRIAGE_REPO_ROOT" in code or "ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER" in code):
                offenders.append(f"{path.relative_to(ROOT)}:{n}")
    assert offenders == []
