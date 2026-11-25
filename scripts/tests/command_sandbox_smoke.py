"""A fresh install runs agents' shell commands inside the OS sandbox (root backlogs 1339 and 1341).

Run by CI's bootstrap smoke with the installed gateway's own Python, after the one-line install:

    <gateway env python> scripts/tests/command_sandbox_smoke.py <gateway url> <data dir> <kind>

It checks the two things a new user depends on: the running gateway reports a command sandbox of
the expected kind (what every client's tool card renders), and a command run through
AbstractCore's ``execute_command`` succeeds inside that sandbox while a refused folder stays
closed to it.

Which workspace settings it runs follows what the gateway reports:

- state ``sandboxed`` (AbstractGateway 0.24.0 and newer on Windows; macOS and Linux with
  bubblewrap): each of the three settings, "Allow everything, refuse listed workspaces" with read
  & write by default, the same with read-only by default, and "Deny everything, allow listed
  workspaces". Under the two write-limited settings a write outside the run's workspace fails and
  a write inside it succeeds.
- state ``partial`` (AbstractGateway 0.23.x on Windows: one setting): the first setting only.

Everything it writes is under a temporary folder of its own, two levels deep.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import urllib.request

# (posture, default mode): the default policy first; the other two limit writes to the rows.
SHAPES = [("any_except_denied", "rw"), ("any_except_denied", "ro"), ("allowed_only", "rw")]


def gateway_report(url: str, data_dir: str) -> dict:
    with open(os.path.join(data_dir, "auth", "bootstrap-admin-token"), encoding="utf-8") as f:
        token = f.read().strip()
    request = urllib.request.Request(
        url.rstrip("/") + "/api/gateway/discovery/tools", headers={"Authorization": "Bearer " + token}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["command_sandbox"]


def _summary(result: dict) -> str:
    return json.dumps({k: result.get(k) for k in ("success", "return_code", "stdout", "stderr", "error")})


def run_commands(kind: str, shapes: list) -> None:
    from abstractcore.tools.common_tools import execute_command
    from abstractcore.tools.sandbox import SandboxSpec

    # Two levels below the temporary folder: a refusal also writes on the refused folder's parent.
    lab = os.path.join(tempfile.mkdtemp(prefix="command-sandbox-smoke-"), "lab")
    refused = os.path.join(lab, "refused")
    os.makedirs(refused)
    secret = os.path.join(refused, "secret.txt")
    with open(secret, "w", encoding="utf-8") as f:
        f.write("refused-content")
    show = "type" if os.name == "nt" else "cat"

    for n, (posture, default_mode) in enumerate(shapes):
        name = f"{posture}/{default_mode}"
        # One workspace per setting: under the write-limited settings the sandbox marks it as theirs.
        workspace = os.path.join(lab, f"workspace-{n}")
        os.makedirs(workspace)
        stamp = SandboxSpec(
            private_workspace=workspace, posture=posture, default_mode=default_mode, refused=(refused,)
        ).to_stamp()

        def run(command: str) -> dict:
            return execute_command(command, working_directory=workspace, timeout=300, _sandbox=stamp)

        ok = run("echo sandbox-ok")
        print(f"[{name}] command:", json.dumps({k: ok.get(k) for k in ("success", "return_code", "stdout", "stderr", "error", "sandbox")}))
        assert ok.get("success") and "sandbox-ok" in (ok.get("stdout") or ""), f"[{name}] the command did not run"
        assert (ok.get("sandbox") or {}).get("kind") == kind, f"[{name}] the command ran under {ok.get('sandbox')}, expected {kind}"

        closed = run(f'{show} "{secret}"')
        said = (closed.get("stdout") or "") + (closed.get("stderr") or "")
        print(f"[{name}] refused folder:", json.dumps({"success": closed.get("success"), "return_code": closed.get("return_code")}))
        assert not closed.get("success") and "refused-content" not in said, f"[{name}] a refused folder was readable"
        with open(secret, encoding="utf-8") as f:  # the control: it is there, and this process reads it
            assert f.read() == "refused-content"

        if (posture, default_mode) == ("any_except_denied", "rw"):
            continue
        # Writes are limited to the run's workspace: next to it (in this script's own folder) fails.
        outside = os.path.join(lab, f"outside-{n}.txt")
        blocked = run(f'echo outside> "{outside}"')
        print(f"[{name}] write outside the workspace:", _summary(blocked))
        assert not os.path.exists(outside), f"[{name}] a command wrote outside the run's workspace"
        inside = os.path.join(workspace, "inside.txt")
        wrote = run(f'echo inside> "{inside}"')
        print(f"[{name}] write inside the workspace:", _summary(wrote))
        assert wrote.get("success") and os.path.exists(inside), f"[{name}] a command could not write its own workspace"


def main(argv: list) -> int:
    url, data_dir, kind = argv[1:4]
    report = gateway_report(url, data_dir)
    print("gateway:", json.dumps({k: report.get(k) for k in ("state", "kind", "kinds", "line")}))
    state = report.get("state")
    assert report.get("kind") == kind, f"the gateway reports {report.get('kind')}, expected {kind}"
    assert state in ("sandboxed", "partial"), f"the gateway reports state {state}"
    kinds = report.get("kinds") or {}
    assert kinds.get("any_except_denied") == kind
    if state == "sandboxed":
        assert kinds.get("allowed_only") == kind, f"state sandboxed, but 'Deny everything' runs under {kinds.get('allowed_only')}"
        shapes = SHAPES
    else:  # one setting sandboxed (AbstractGateway 0.23.x on Windows): the default policy only
        shapes = SHAPES[:1]
    run_commands(kind, shapes)
    print(f"ok: commands run inside {kind} under {len(shapes)} workspace setting(s): " + ", ".join(f"{p}/{m}" for p, m in shapes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
