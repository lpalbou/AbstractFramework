"""Bridge clean Quit for an already-running, pre-policy stack supervisor.

The assistant launchers select this only when their parent owns af_stack.pid
and lacks the on-failure capability. Current supervisors exec the GUI directly.
A clean GUI exit leaves only this small, dormant process until its owning stack
stops; a failure propagates unchanged to the old supervisor's crash recovery.
No files, background jobs or machine persistence are installed.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from collections.abc import Sequence


def supervise(command: Sequence[str], *, parent: int | None = None) -> int:
    owner = os.getppid() if parent is None else parent
    stopping = 0

    def stop(signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = signum

    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
    child: subprocess.Popen | None = None
    try:
        child = subprocess.Popen(command)
        print(f"[assistant launcher] legacy supervisor {owner}; GUI pid {child.pid}", flush=True)
        while child.poll() is None:
            if stopping or os.getppid() != owner:
                break
            time.sleep(0.1)
        if stopping or os.getppid() != owner:
            return 128 + (stopping or signal.SIGTERM)
        status = child.wait()
        if status != 0:
            return status if status > 0 else 128 - status
        print("[assistant launcher] Quit received; GUI stopped. Legacy supervisor guard is dormant until stack shutdown.", flush=True)
        while not stopping and os.getppid() == owner:
            time.sleep(0.2)
        return 128 + stopping if stopping else 0
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    raise SystemExit(supervise([sys.executable, "-m", "abstractassistant.cli", *sys.argv[1:]]))
