#!/usr/bin/env python3
"""Check live remote main against every inventoried checkout; never change checkouts.

Default: strict handoff check. --development permits edits/feature commits that
contain live remote main. --run COMMAND... guards a build or redeploy before and
after execution, refusing success if the source snapshot changed in between.
Only Git and the Python standard library are required.
"""

from __future__ import annotations

import argparse
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from af_inventory import ManifestError, load_manifest  # noqa: E402


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True,
        timeout=45, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if result.returncode:
        # Avoid echoing URLs/credentials in transport diagnostics.
        raise RuntimeError(f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout.strip()


def snapshot(repo: Path) -> dict:
    head = git(repo, "rev-parse", "HEAD")
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    status = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    hidden = [entry for entry in git(repo, "ls-files", "-v", "-z").split("\0")
              if entry and (entry[0].islower() or entry.startswith("S "))]
    digest = hashlib.sha256()
    for args in [("diff", "--binary", "HEAD"), ("diff", "--binary", "--cached")]:
        digest.update(git(repo, *args).encode())
    for name in git(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
        if not name:
            continue
        path = repo / name
        digest.update(name.encode())
        if path.is_symlink():
            digest.update(os.readlink(path).encode())
        elif path.is_file():
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        else:
            # Nested untracked repositories are dirty regardless of their contents.
            digest.update(b"directory")
    return {"head": head, "branch": branch, "status": status,
            "hidden_index_entries": hidden, "changes_sha256": digest.hexdigest()}


def inspect(repo: Path, name: str, development: bool, root_dirty_reason: str) -> dict:
    row = {"repo": name, "path": str(repo), "errors": []}
    try:
        if not (repo / ".git").exists():
            raise RuntimeError("checkout missing (run scripts/clone.sh)")
        if Path(git(repo, "rev-parse", "--show-toplevel")).resolve() != repo.resolve():
            raise RuntimeError("path is not this repository's checkout root")
        before = snapshot(repo)
        remote = git(repo, "ls-remote", "--exit-code", "origin", "refs/heads/main")
        fields = remote.split()
        if len(fields) != 2 or fields[1] != "refs/heads/main":
            raise RuntimeError("origin did not return exactly one main ref")
        row.update(before, remote_main=fields[0])
        if snapshot(repo) != before:
            raise RuntimeError("checkout changed during remote observation; retry")
        if development:
            try:
                git(repo, "merge-base", "--is-ancestor", fields[0], before["head"])
            except RuntimeError:
                row["errors"].append("HEAD does not contain live origin/main; fetch and integrate first")
        else:
            if before["hidden_index_entries"]:
                row["errors"].append("index has assume-unchanged/skip-worktree entries hiding source state")
            if before["branch"] != "main":
                row["errors"].append("checkout is not on main")
            if before["head"] != fields[0]:
                row["errors"].append("HEAD differs from live origin/main (ahead, behind or diverged)")
            if git(repo, "rev-parse", "--abbrev-ref", "@{upstream}") != "origin/main":
                row["errors"].append("main must track origin/main")
            if before["status"]:
                if name == "." and root_dirty_reason:
                    row["root_dirty_exception"] = root_dirty_reason
                else:
                    row["errors"].append("checkout has staged, modified or untracked files")
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        row["errors"].append(str(exc) if not isinstance(exc, subprocess.TimeoutExpired) else "git timed out")
    return row


def check(root: Path, development: bool, root_dirty_reason: str) -> dict:
    manifest = root / "scripts/lib/packages.txt"
    manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    repos = list(dict.fromkeys(p.repo for p in load_manifest(manifest)))
    if "." not in repos:
        raise ValueError("inventory must include the framework root")
    for name in repos:
        path = (root / name).resolve()
        if path != root and root not in path.parents:
            raise ValueError(f"inventory checkout escapes workspace: {name}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda name: inspect(root / name, name, development, root_dirty_reason), repos))
    errors = []
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != manifest_hash:
        errors.append("inventory changed during check")
    for row in rows:
        if row["errors"]:
            continue
        try:
            # Detect edits in an early repo while later repositories were queried.
            if snapshot(Path(row["path"])) != {k: row[k] for k in snapshot_keys()}:
                row["errors"].append("checkout changed during workspace check; retry")
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            row["errors"].append("checkout became unreadable during workspace check")
    return {"checked_at": datetime.now(timezone.utc).isoformat(), "root": str(root),
            "mode": "development" if development else "handoff", "inventory_sha256": manifest_hash,
            "repos": rows, "errors": errors, "ok": not errors and all(not r["errors"] for r in rows)}


def snapshot_keys() -> tuple:
    return ("head", "branch", "status", "changes_sha256", "hidden_index_entries")


def identity(report: dict) -> tuple:
    return (report["inventory_sha256"], [(r["repo"], r.get("remote_main"),
            tuple(r.get(k) for k in snapshot_keys())) for r in report["repos"]])


def write_receipt(path: Path | None, report: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    os.replace(stream.name, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--development", action="store_true", help="allow local work containing live remote main")
    parser.add_argument("--allow-root-dirty", default="", metavar="REASON", help="handoff only: record held root edits; never exempt root freshness")
    parser.add_argument("--receipt", type=Path, help="write JSON on both success and failure; keep outside tracked source")
    parser.add_argument("--verify-receipt", type=Path, action="append", default=[],
                        help="require a prior successful guarded command on these exact sources/remotes (repeatable)")
    parser.add_argument("--run", nargs=argparse.REMAINDER, help="execute argv only after a passing check, then recheck")
    args = parser.parse_args()
    if args.run == []:
        parser.error("--run requires a command")
    if args.development and args.allow_root_dirty:
        parser.error("--allow-root-dirty applies only to handoff checks")
    if args.development and args.verify_receipt:
        parser.error("--verify-receipt is a strict handoff operation")
    if args.receipt and any(p.resolve() == args.receipt.resolve() for p in args.verify_receipt):
        parser.error("output receipt must differ from the receipts being verified")
    report = {"ok": False, "errors": ["check did not complete"]}
    write_receipt(args.receipt, report)  # Invalidate a prior successful receipt immediately.
    try:
        report = check(args.root.resolve(), args.development, args.allow_root_dirty.strip())
        report["verified_receipts"] = []
        for path in args.verify_receipt:
            prior = json.loads(path.read_text())
            if (not isinstance(prior, dict) or not prior.get("ok")
                    or prior.get("mode") != "handoff" or prior.get("command_exit") != 0
                    or not isinstance(prior.get("before"), dict) or not prior["before"].get("ok")
                    or prior.get("root") != report["root"]):
                report["errors"].append(f"{path}: not a successful strict guarded-command receipt for this workspace")
            elif identity(prior) != identity(report):
                report["errors"].append(f"{path}: sources/remotes differ from the validated command; rerun it")
            else:
                report["verified_receipts"].append(str(path.resolve()))
        report["ok"] = report["ok"] and not report["errors"]
        if report["ok"] and args.run:
            write_receipt(args.receipt, {**report, "ok": False, "phase": "command-running"})
            completed = subprocess.run(args.run, cwd=args.root.resolve())
            after = check(args.root.resolve(), args.development, args.allow_root_dirty.strip())
            if identity(report) != identity(after):
                after["errors"].append("source or remote main changed during command; rebuild/redeploy and recheck")
            after["command_exit"] = completed.returncode
            after["command"] = args.run
            after["before"] = report
            after["ok"] = after["ok"] and not after["errors"] and completed.returncode == 0
            report = after
    except (OSError, ValueError, RuntimeError, ManifestError, KeyError, TypeError, KeyboardInterrupt) as exc:
        report = {"ok": False, "errors": [f"check/command failed: {type(exc).__name__}: {exc}"]}
    write_receipt(args.receipt, report)
    for row in report.get("repos", []):
        for error in row["errors"]:
            print(f"FAIL {row['repo']}: {error}", file=sys.stderr)
    for error in report.get("errors", []):
        print(f"FAIL: {error}", file=sys.stderr)
    if report.get("command_exit", 0):
        print(f"FAIL: guarded command exited {report['command_exit']}", file=sys.stderr)
    print(f"Workspace {report.get('mode', 'check')}: {'PASS' if report['ok'] else 'FAIL'}")
    if not report["ok"]:
        print("Use scripts/pull.sh for safe fast-forwards; resolve divergence/edits explicitly. No checkout was changed by this check.", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
