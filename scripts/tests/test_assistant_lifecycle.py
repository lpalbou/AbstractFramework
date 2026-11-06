"""Legacy-parent migration: real children, no GUI or production services."""
from pathlib import Path
import os
import select
import signal
import subprocess
import sys
import time

import pytest

LIB = Path(__file__).resolve().parents[1] / "lib"
DRIVER = """
import sys
sys.path.insert(0, sys.argv[1])
from assistant_legacy_supervisor import supervise
raise SystemExit(supervise([sys.executable, '-c', sys.argv[2]]))
"""


def start(code):
    return subprocess.Popen([sys.executable, "-u", "-c", DRIVER, str(LIB), code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def line(proc):
    assert select.select([proc.stdout], [], [], 5)[0], "child did not report within 5s"
    return proc.stdout.readline().decode()


def stop(proc):
    if proc.poll() is None:
        proc.terminate()
    proc.communicate(timeout=5)


def test_clean_quit_stays_closed_until_stack_stops():
    proc = start("pass")
    try:
        assert "GUI pid" in line(proc)
        assert "GUI stopped" in line(proc)
        with pytest.raises(subprocess.TimeoutExpired):
            proc.wait(timeout=0.5)
        proc.terminate()
        assert proc.wait(timeout=4) == 143
    finally:
        stop(proc)


@pytest.mark.parametrize("code,status", [("raise SystemExit(7)", 7), ("import os,signal; os.kill(os.getpid(), signal.SIGTERM)", 143)])
def test_crashes_propagate_to_existing_supervisor(code, status):
    proc = start(code)
    try:
        assert proc.wait(timeout=5) == status
    finally:
        stop(proc)


def test_stop_forwards_and_reaps_even_stubborn_child(tmp_path):
    ready = tmp_path / "ready"
    proc = start(f"import os,signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); open({str(ready)!r},'w').write(str(os.getpid())); time.sleep(60)")
    try:
        line(proc)
        for _ in range(100):
            if ready.exists():
                break
            time.sleep(0.02)
        child = int(ready.read_text())
        proc.terminate()
        assert proc.wait(timeout=4) == 143
        with pytest.raises(ProcessLookupError):
            os.kill(child, 0)
    finally:
        stop(proc)


@pytest.mark.parametrize("code", ["pass", "import time; time.sleep(60)"])
def test_guard_ends_when_owning_parent_disappears(tmp_path, code):
    # A session-local owner exits normally without forwarding any signal.
    # The wrapper must notice reparenting, reap its GUI and stop by itself.
    done = tmp_path / "done"
    detached = DRIVER.replace("raise SystemExit(supervise([sys.executable, '-c', sys.argv[2]]))", f"status = supervise([sys.executable, '-c', sys.argv[2]]); open({str(done)!r}, 'w').write(str(status))")
    owner = subprocess.Popen([sys.executable, "-c", "import subprocess,sys; p=subprocess.Popen(sys.argv[1:]); import time; time.sleep(0.5)", sys.executable, "-u", "-c", detached, str(LIB), code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = owner.communicate(timeout=6)
    assert owner.returncode == 0, err
    assert done.exists(), out


@pytest.mark.parametrize("policy,owns,expected", [("", True, 0), ("on-failure", True, 1), ("always", True, 1), ("", False, 1)])
def test_only_exact_legacy_parent_uses_guard(tmp_path, policy, owns, expected):
    # The test process is the child shell's actual PPID.
    (tmp_path / "af_stack.pid").write_text(str(os.getpid() if owns else os.getpid() + 100000))
    env = dict(os.environ, RUNTIME_DIR=str(tmp_path), AF_SUPERVISOR_RESTART_POLICY=policy)
    result = subprocess.run(["bash", "-c", 'source "$1/assistant_lifecycle.sh"; assistant_needs_legacy_guard', "_", str(LIB)], env=env)
    assert result.returncode == expected
