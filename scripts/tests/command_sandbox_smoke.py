"""A fresh install runs agents' shell commands inside the OS sandbox (root backlog 1339).

Run by CI's bootstrap smoke with the installed gateway's own Python, after the one-line install:

    <gateway env python> scripts/tests/command_sandbox_smoke.py <gateway url> <data dir> <kind>

It checks the two things a new user depends on: the running gateway reports a command sandbox of
the expected kind (what every client's tool card renders), and a command run through
AbstractCore's ``execute_command`` under the default workspace policy ("Allow everything, refuse
listed workspaces", read & write) succeeds inside that sandbox while a refused folder stays
closed to it. Everything it writes is under a temporary folder of its own.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import urllib.request


def gateway_report(url: str, data_dir: str) -> dict:
    with open(os.path.join(data_dir, "auth", "bootstrap-admin-token"), encoding="utf-8") as f:
        token = f.read().strip()
    request = urllib.request.Request(
        url.rstrip("/") + "/api/gateway/discovery/tools", headers={"Authorization": "Bearer " + token}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["command_sandbox"]


def run_commands(kind: str) -> None:
    from abstractcore.tools.common_tools import execute_command
    from abstractcore.tools.sandbox import SandboxSpec

    # Two levels below the temporary folder: a refusal also writes on the refused folder's parent.
    lab = os.path.join(tempfile.mkdtemp(prefix="command-sandbox-smoke-"), "lab")
    workspace = os.path.join(lab, "workspace")
    refused = os.path.join(lab, "refused")
    for folder in (workspace, refused):
        os.makedirs(folder)
    secret = os.path.join(refused, "secret.txt")
    with open(secret, "w", encoding="utf-8") as f:
        f.write("refused-content")

    stamp = SandboxSpec(
        private_workspace=workspace, posture="any_except_denied", default_mode="rw", refused=(refused,)
    ).to_stamp()
    show = "type" if os.name == "nt" else "cat"

    ok = execute_command("echo sandbox-ok", working_directory=workspace, timeout=120, _sandbox=stamp)
    print("command:", json.dumps({k: ok.get(k) for k in ("success", "return_code", "stdout", "stderr", "error", "sandbox")}))
    assert ok.get("success") and "sandbox-ok" in (ok.get("stdout") or ""), "the command did not run"
    assert (ok.get("sandbox") or {}).get("kind") == kind, f"the command ran under {ok.get('sandbox')}, expected {kind}"

    closed = execute_command(f'{show} "{secret}"', working_directory=workspace, timeout=120, _sandbox=stamp)
    said = (closed.get("stdout") or "") + (closed.get("stderr") or "")
    print("refused folder:", json.dumps({"success": closed.get("success"), "return_code": closed.get("return_code")}))
    assert not closed.get("success") and "refused-content" not in said, "a refused folder was readable"
    with open(secret, encoding="utf-8") as f:  # the control: it is there, and this process reads it
        assert f.read() == "refused-content"


def main(argv: list) -> int:
    url, data_dir, kind = argv[1:4]
    report = gateway_report(url, data_dir)
    print("gateway:", json.dumps({k: report.get(k) for k in ("state", "kind", "kinds", "line")}))
    assert report.get("kind") == kind, f"the gateway reports {report.get('kind')}, expected {kind}"
    assert report.get("state") in ("sandboxed", "partial"), f"the gateway reports state {report.get('state')}"
    assert (report.get("kinds") or {}).get("any_except_denied") == kind
    run_commands(kind)
    print("ok: commands run inside", kind)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
