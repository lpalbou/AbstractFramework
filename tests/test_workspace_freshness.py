"""Real Git regression tests; all remotes are local bare repositories."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def git(path, *args, env):
    return subprocess.check_output(["git", "-C", str(path), *args], env=env, text=True).strip()


@pytest.fixture
def workspace(tmp_path):
    config = tmp_path / "gitconfig"
    config.write_text('[user]\nname = test\nemail = test@example.invalid\n[init]\ndefaultBranch = main\n')
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(config)}
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(key, None)
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "scripts/lib").mkdir(parents=True)
    shutil.copy(SCRIPTS / "check_workspace.py", root / "scripts")
    shutil.copy(SCRIPTS / "lib/af_inventory.py", root / "scripts/lib")
    shutil.copy(SCRIPTS / "status.sh", root / "scripts")
    shutil.copy(SCRIPTS / "lib/repo_groups.sh", root / "scripts/lib")
    (root / "scripts/lib/packages.txt").write_text(
        'alpha|alpha|test/alpha|npm|.|npm|@test/alpha|0|-\n'
        'root|.|test/root|meta|.|pypi|root|1|alpha:pin\n'
    )
    (root / ".gitignore").write_text('alpha/\nuntracked/\n__pycache__/\n')
    (root / "alpha").mkdir()
    (root / "alpha/file.txt").write_text("initial\n")
    for name, path in [("root", root), ("alpha", root / "alpha")]:
        git(path, "init", env=env)
        git(path, "add", ".", env=env)
        git(path, "commit", "-m", "initial", env=env)
        remote = tmp_path / f"{name}.git"
        subprocess.run(["git", "init", "--bare", str(remote)], env=env, check=True, capture_output=True)
        git(path, "remote", "add", "origin", str(remote), env=env)
        git(path, "push", "-u", "origin", "main", env=env)
    return root, env, tmp_path / "receipt.json"


def check(workspace, *args):
    root, env, receipt = workspace
    result = subprocess.run(
        [sys.executable, str(root / "scripts/check_workspace.py"), "--receipt", str(receipt), *args],
        env=env, text=True, capture_output=True,
    )
    return result, json.loads(receipt.read_text())


def advance_remote(workspace):
    root, env, _ = workspace
    other = root.parent / "other"
    subprocess.run(["git", "clone", str(root.parent / "alpha.git"), str(other)],
                   env=env, check=True, capture_output=True)
    (other / "remote.txt").write_text("upstream\n")
    git(other, "add", ".", env=env)
    git(other, "commit", "-m", "upstream", env=env)
    git(other, "push", env=env)
    return git(other, "rev-parse", "HEAD", env=env)


def test_clean_workspace_and_guarded_command(workspace):
    result, report = check(workspace, "--run", sys.executable, "-c", "print('ran command')")
    assert result.returncode == 0, result.stderr
    assert report["ok"] and report["before"]["ok"] and report["command_exit"] == 0
    assert len(report["repos"]) == 2
    assert all(row["head"] == row["remote_main"] for row in report["repos"])


def test_live_remote_detects_stale_cache_without_moving_checkout(workspace):
    root, env, _ = workspace
    old = git(root / "alpha", "rev-parse", "HEAD", env=env)
    new = advance_remote(workspace)
    marker = root.parent / "must-not-run"
    result, report = check(workspace, "--run", sys.executable, "-c",
                           f"from pathlib import Path; Path({str(marker)!r}).touch()")
    assert result.returncode == 1 and not report["ok"] and not marker.exists()
    assert report["repos"][0]["remote_main"] == new
    assert git(root / "alpha", "rev-parse", "HEAD", env=env) == old
    assert git(root / "alpha", "rev-parse", "origin/main", env=env) == old


@pytest.mark.parametrize("case", ["missing", "remote-failure", "dirty", "untracked", "ahead", "branch", "detached", "no-upstream"])
def test_handoff_fails_closed(workspace, case):
    root, env, _ = workspace
    repo = root / "alpha"
    if case == "missing":
        repo.rename(root.parent / "saved-alpha")
    elif case == "remote-failure":
        git(repo, "remote", "set-url", "origin", str(root.parent / "absent.git"), env=env)
    elif case == "dirty":
        (repo / "file.txt").write_text("edit\n")
    elif case == "untracked":
        (repo / "new.txt").write_text("work\n")
    elif case == "ahead":
        git(repo, "commit", "--allow-empty", "-m", "local only", env=env)
    elif case == "branch":
        git(repo, "switch", "-c", "feature", env=env)
    elif case == "detached":
        git(repo, "checkout", "--detach", env=env)
    elif case == "no-upstream":
        git(repo, "branch", "--unset-upstream", env=env)
    result, report = check(workspace)
    assert result.returncode == 1 and not report["ok"]
    assert report["repos"][0]["errors"]


def test_development_allows_feature_edits_but_not_stale_base(workspace):
    root, env, _ = workspace
    repo = root / "alpha"
    git(repo, "switch", "-c", "feature", env=env)
    git(repo, "commit", "--allow-empty", "-m", "local feature", env=env)
    (repo / "file.txt").write_text("editing\n")
    assert check(workspace, "--development")[0].returncode == 0
    advance_remote(workspace)
    result, report = check(workspace, "--development")
    assert result.returncode == 1 and not report["ok"]


def test_root_dirty_exception_is_narrow_and_named(workspace):
    root, env, _ = workspace
    (root / "candidate.txt").write_text("held candidate\n")
    assert check(workspace)[0].returncode == 1
    result, report = check(workspace, "--allow-root-dirty", "candidate held for operator")
    assert result.returncode == 0
    assert report["repos"][1]["root_dirty_exception"] == "candidate held for operator"
    (root / "alpha/file.txt").write_text("lower package edit\n")
    assert check(workspace, "--allow-root-dirty", "candidate held")[0].returncode == 1
    git(root / "alpha", "restore", "file.txt", env=env)
    git(root, "add", "candidate.txt", env=env)
    git(root, "commit", "-m", "root ahead", env=env)
    assert check(workspace, "--allow-root-dirty", "candidate held")[0].returncode == 1


def test_failed_command_cannot_leave_successful_receipt(workspace):
    assert check(workspace)[1]["ok"]
    result, report = check(workspace, "--run", sys.executable, "-c", "raise SystemExit(7)")
    assert result.returncode == 1 and not report["ok"] and report["command_exit"] == 7


def test_source_change_during_guarded_command_invalidates_handoff(workspace):
    root, _, _ = workspace
    (root / "candidate.txt").write_text("before\n")
    result, report = check(workspace, "--allow-root-dirty", "held root candidate", "--run",
                           sys.executable, "-c", "from pathlib import Path; Path('candidate.txt').write_text('after')")
    assert result.returncode == 1 and not report["ok"]
    assert any("changed during command" in error for error in report["errors"])


def test_remote_merge_during_command_invalidates_handoff(workspace):
    result, report = check(workspace, "--run", sys.executable, "-c",
        "import subprocess; from pathlib import Path; "
        "r = Path('../alpha.git').resolve(); "
        "subprocess.run(['git', 'clone', str(r), '../remote-worker'], check=True); "
        "subprocess.run(['git', '-C', '../remote-worker', 'commit', '--allow-empty', '-m', 'remote merge'], check=True); "
        "subprocess.run(['git', '-C', '../remote-worker', 'push'], check=True)")
    assert result.returncode == 1 and not report["ok"]
    assert any("changed during command" in error for error in report["errors"])


def test_missing_inventory_invalidates_previous_receipt(workspace):
    assert check(workspace)[1]["ok"]
    root, _, _ = workspace
    (root / "scripts/lib/packages.txt").rename(root / "scripts/lib/packages.saved")
    result, report = check(workspace)
    assert result.returncode != 0 and not report["ok"]


def test_status_check_fails_even_when_cached_overview_is_clean(workspace):
    root, env, _ = workspace
    advance_remote(workspace)
    result = subprocess.run(["bash", str(root / "scripts/status.sh"), "--check"],
                            env=env, text=True, capture_output=True)
    assert result.returncode == 1
    assert "HEAD differs from live origin/main" in result.stderr


def test_malformed_inventory_reports_failure(workspace):
    root, _, _ = workspace
    (root / "scripts/lib/packages.txt").write_text("malformed\n")
    result, report = check(workspace)
    assert result.returncode == 1 and not report["ok"]
    assert "ManifestError" in report["errors"][0]


def test_handoff_rejects_build_receipt_after_pull_even_when_main_is_current(workspace):
    root, env, receipt = workspace
    assert check(workspace, "--run", sys.executable, "-c", "pass")[1]["ok"]
    built = root.parent / "build.json"
    shutil.copy(receipt, built)
    assert check(workspace, "--verify-receipt", str(built))[0].returncode == 0
    advance_remote(workspace)
    git(root / "alpha", "pull", "--ff-only", env=env)
    assert check(workspace)[0].returncode == 0
    result, report = check(workspace, "--verify-receipt", str(built))
    assert result.returncode == 1 and not report["ok"]
    assert "sources/remotes differ" in report["errors"][0]


@pytest.mark.parametrize("flags", [[], ["--development", "--run", sys.executable, "-c", "pass"]])
def test_plain_check_or_development_receipt_cannot_certify_a_candidate_build(workspace, flags):
    root, _, receipt = workspace
    assert check(workspace, *flags)[1]["ok"]
    prior = root.parent / "not-a-build.json"
    shutil.copy(receipt, prior)
    result, report = check(workspace, "--verify-receipt", str(prior))
    assert result.returncode == 1 and not report["ok"]


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_hidden_tracked_edits_cannot_pass_handoff(workspace, flag):
    root, env, receipt = workspace
    assert check(workspace, "--run", sys.executable, "-c", "pass")[1]["ok"]
    built = root.parent / "build.json"
    shutil.copy(receipt, built)
    git(root / "alpha", "update-index", flag, "file.txt", env=env)
    (root / "alpha/file.txt").write_text("hidden change\n")
    assert git(root / "alpha", "status", "--porcelain", env=env) == ""
    result, report = check(workspace, "--verify-receipt", str(built))
    assert result.returncode == 1 and not report["ok"]
    assert "hiding source state" in report["repos"][0]["errors"][0]


def test_build_deploy_handoff_chain_and_later_root_edit(workspace):
    root, _, receipt = workspace
    (root / "candidate.txt").write_text("held candidate\n")
    exception = ["--allow-root-dirty", "held root candidate"]
    assert check(workspace, *exception, "--run", sys.executable, "-c", "pass")[1]["ok"]
    built = root.parent / "build.json"
    shutil.copy(receipt, built)
    assert check(workspace, *exception, "--verify-receipt", str(built),
                 "--run", sys.executable, "-c", "pass")[1]["ok"]
    deployed = root.parent / "deploy.json"
    shutil.copy(receipt, deployed)
    verification = ["--verify-receipt", str(built), "--verify-receipt", str(deployed)]
    assert check(workspace, *exception, *verification)[1]["ok"]
    (root / "candidate.txt").write_text("a different candidate\n")
    result, report = check(workspace, *exception, *verification)
    assert result.returncode == 1 and not report["ok"]
    assert len(report["errors"]) == 2
