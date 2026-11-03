"""scripts/ci_local.py reads GitHub Actions workflows the way GitHub does (docs/ci-local.md)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("ci_local", ROOT / "scripts" / "ci_local.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ci_local"] = module
    spec.loader.exec_module(module)
    return module


ci = _load()


def ctx(**data):
    base = {"github": {"event_name": "pull_request", "base_ref": "main", "event": {"inputs": None}},
            "env": {}, "matrix": {}, "needs": {}, "steps": {}, "inputs": {}, "secrets": {}, "runner": {"os": "macOS"}}
    base.update(data)
    return ci.Context(base)


@pytest.mark.parametrize(
    "expr, expected",
    [
        ("github.event_name == 'pull_request'", True),
        ("github.event_name == 'PULL_REQUEST'", True),  # string comparison ignores case
        ("github.event_name != 'pull_request'", False),
        ("github.event.inputs.cpu_max || '10'", "10"),
        ("matrix.python-version == '3.12'", True),
        ("!(1 == 2) && 'a'", "a"),
        ("startsWith(github.ref, 'refs/tags/v')", False),
        ("contains(fromJSON('[\"3.12\", \"3.13\"]'), '3.13')", True),
        ("format('{0}-{1}', 'a', 1)", "a-1"),
        ("fromJSON(github.event_name == 'pull_request' && '[\"3.12\"]' || '[\"3.10\", \"3.11\"]')", ["3.12"]),
        ("needs.changes.outputs.tui == 'true'", False),
        ("runner.os != 'Windows'", True),
        ("1 < 2 && '3' == 3", True),
    ],
)
def test_expressions(expr, expected):
    c = ctx(github={"event_name": "pull_request", "ref": "refs/pull/0/merge", "event": {"inputs": None}},
            matrix={"python-version": "3.12"}, needs={"changes": {"outputs": {"tui": "false"}}})
    assert ci.evaluate(expr, c) == expected


def test_interpolation_keeps_the_type_of_a_whole_expression():
    c = ctx()
    assert ci.interpolate("${{ fromJSON('[1, 2]') }}", c) == [1, 2]
    assert ci.interpolate("base origin/${{ github.base_ref }}", c) == "base origin/main"


def test_if_conditions_imply_success_unless_they_name_a_status_function():
    c = ci.Context({"runner": {"os": "macOS"}}, status=lambda name: name == "always")
    assert ci.condition("runner.os != 'Windows'", c) is False  # success() is false here
    assert ci.condition("always() && runner.os != 'Windows'", c) is True
    assert ci.condition(None, ci.Context({})) is True


def test_secrets_are_found_in_any_expression():
    spec = {"steps": [{"env": {"K": "${{ secrets.ASC_KEY_ID }}"}}, {"run": "echo ${{ github.sha }}"}]}
    assert ci.secrets_in(spec) == {"ASC_KEY_ID"}


@pytest.mark.parametrize(
    "patterns, path, expected",
    [
        (["src/**"], "src/a/b.py", True),
        (["src/**"], "tests/a.py", False),
        (["*.toml"], "pyproject.toml", True),
        (["*.toml"], "a/pyproject.toml", False),
        (["**/README.md"], "README.md", True),
        (["**/README.md"], "docs/README.md", True),
        (["phone/iphone/**", "!phone/iphone/docs/**"], "phone/iphone/docs/a.md", False),
        (["v*"], "v1.2.3", True),
    ],
)
def test_filter_patterns(patterns, path, expected):
    assert ci.filter_matches(patterns, path) is expected


def test_triggers_follow_branch_tag_and_path_filters():
    on = {"push": {"branches": ["main"], "tags": ["v*"]}, "pull_request": {"paths": ["src/**"]}}
    assert ci.triggered(on, "push", "refs/heads/main", "main", [])[0]
    assert not ci.triggered(on, "push", "refs/heads/feature", "main", [])[0]
    assert ci.triggered(on, "push", "refs/tags/v1.0.0", "main", [])[0]
    assert ci.triggered(on, "pull_request", "refs/pull/0/merge", "main", ["src/x.py"])[0]
    assert not ci.triggered(on, "pull_request", "refs/pull/0/merge", "main", ["docs/x.md"])[0]
    assert not ci.triggered({"workflow_dispatch": None}, "push", "refs/heads/main", "main", [])[0]
    assert ci.triggered("pull_request", "pull_request", "refs/pull/0/merge", "main", [])[0]
    # A tag push does not run a workflow whose push filter names only branches.
    assert not ci.triggered({"push": {"branches": ["main"]}}, "push", "refs/tags/v1", "main", [])[0]


def test_matrix_expansion_with_include_exclude_and_expressions():
    c = ctx(github={"event_name": "push"})
    strategy = {"matrix": {
        "python-version": "${{ fromJSON(github.event_name == 'pull_request' && '[\"3.12\"]' || '[\"3.10\", \"3.12\"]') }}",
        "shard": [0, 1],
        "exclude": [{"python-version": "3.10", "shard": 1}],
        "include": [{"python-version": "3.12", "extra": "yes"}, {"python-version": "3.9"}],
    }}
    combos = ci.expand_matrix(strategy, c)
    assert {"python-version": "3.10", "shard": 0} in combos
    assert {"python-version": "3.10", "shard": 1} not in combos
    # An include adds its new keys to every combination it does not contradict...
    assert {"python-version": "3.12", "shard": 0, "extra": "yes"} in combos
    # ...and becomes a combination of its own when it matches none.
    assert {"python-version": "3.9"} in combos
    assert len(combos) == 4
    assert ci.expand_matrix({"matrix": {"py": ["3.12"], "include": [{"os": "macos-latest"}]}}, c) == [
        {"py": "3.12", "os": "macos-latest"}]
    assert ci.expand_matrix(None, c) == [{}]


def test_pip_commands_run_through_uv_pip():
    script = 'python -m pip install -U pip\npython3 -m pip install --no-cache-dir -e ".[dev]"\npip install build\nmypip install x'
    out = ci.translate_pip(script, "/u/uv")
    assert out.splitlines() == [
        "/u/uv pip install -U pip",
        '/u/uv pip install --no-cache -e ".[dev]"',
        "/u/uv pip install build",
        "mypip install x",
    ]


def test_shells():
    assert ci.shell_command(None, "s.sh") == ["bash", "-e", "s.sh"]
    assert ci.shell_command("bash", "s.sh") == ["bash", "--noprofile", "--norc", "-eo", "pipefail", "s.sh"]
    assert ci.shell_command("python", "s.sh") == ["python", "s.sh"]
    assert ci.shell_command("pwsh", "s.sh") is None


def test_env_files(tmp_path):
    f = tmp_path / "out"
    f.write_text("a=1\nb<<EOF\nline 1\nline 2\nEOF\nc=x=y\n", encoding="utf-8")
    assert ci.parse_env_file(f) == {"a": "1", "b": "line 1\nline 2", "c": "x=y"}


def test_runners():
    assert ci.runner_verdict("ubuntu-latest")[0]
    assert ci.runner_verdict("macos-latest")[0]
    assert not ci.runner_verdict("windows-latest")[0]
    assert not ci.runner_verdict("xcode-27")[0]
    assert ci.runner_verdict("xcode-27", ["xcode-27"])[0]


def _job(spec, wf=None):
    return ci.Job("CI", "ci.yml", wf or {}, "j", spec, {}, "ci/j")


def test_jobs_that_cannot_run_here_say_why_and_unknown_actions_are_errors():
    assert ci.static_skip(_job({"steps": [{"uses": "actions/checkout@v4"}, {"run": "true"}]})) is None
    assert ci.static_skip(_job({"steps": [{"uses": "docker/build-push-action@v6"}]}))[0] == "SKIPPED"
    assert ci.static_skip(_job({"environment": "pypi", "steps": []}))[0] == "SKIPPED"
    assert ci.static_skip(_job({"services": {"db": {}}, "steps": []}))[0] == "SKIPPED"
    assert ci.static_skip(_job({"steps": [{"env": {"T": "${{ secrets.T }}"}, "run": "x"}]}))[0] == "SKIPPED"
    kind, reason = ci.static_skip(_job({"steps": [{"uses": "someone/new-action@v1"}]}))
    assert kind == "ERROR" and "teach scripts/ci_local.py" in reason
    assert ci.static_skip(_job({"uses": "org/repo/.github/workflows/x.yml@main"}))[0] == "ERROR"


def test_the_root_shim_marks_the_job(tmp_path):
    import subprocess

    shim = tmp_path / "sudo"
    shim.write_text(ci.ROOT_SHIM, encoding="utf-8")
    shim.chmod(0o755)
    out = subprocess.run([str(shim), "apt-get", "update"], env={"CI_LOCAL_JOB_DIR": str(tmp_path), "PATH": "/usr/bin:/bin"},
                         capture_output=True, text=True)
    assert out.returncode == 97
    assert (tmp_path / "needs-root").read_text(encoding="utf-8").strip() == "sudo apt-get update"


def _schedule(items, needs, serial=(), workers=3, hold=0.05):
    """Fake jobs: each records when it starts and ends; a job holds its worker for `hold` seconds."""
    import threading
    import time

    log, running, peak, lock = [], [0], [0], threading.Lock()
    seen_while_serial = []

    def fn(item):
        with lock:
            running[0] += 1
            peak[0] = max(peak[0], running[0])
            log.append(("start", item))
            if item[0] in serial and running[0] > 1:
                seen_while_serial.append(item)
        time.sleep(hold)
        with lock:
            running[0] -= 1
            log.append(("end", item))

    ci.run_scheduled(items, key_of=lambda i: i[0], needs_of=lambda i: needs.get(i[0], []),
                     serial_of=lambda i: i[0] in serial, workers=workers, fn=fn)
    return log, peak[0], seen_while_serial


def test_scheduler_runs_matrix_entries_in_parallel_and_respects_needs():
    items = [("test", 0), ("test", 1), ("test", 2), ("build", 0), ("tests", 0)]
    log, peak, _ = _schedule(items, {"tests": ["test"]}, workers=3)
    assert peak == 3
    assert len([x for kind, x in log if kind == "start"]) == 5
    # `tests` needs every `test` entry: it starts after all three ended.
    start_tests = log.index(("start", ("tests", 0)))
    assert all(log.index(("end", ("test", i))) < start_tests for i in range(3))


def test_serial_jobs_run_alone_at_the_end_with_what_needs_them():
    items = [("test", 0), ("test", 1), ("local-models", 0), ("after", 0), ("docs", 0)]
    log, peak, overlapped = _schedule(items, {"after": ["local-models"]}, serial={"local-models"}, workers=4)
    assert overlapped == []
    starts = [x for kind, x in log if kind == "start"]
    assert starts[-2:] == [("local-models", 0), ("after", 0)]
    serial_start = log.index(("start", ("local-models", 0)))
    assert all(log.index(("end", x)) < serial_start for x in [("test", 0), ("test", 1), ("docs", 0)])


def test_a_deep_needs_chain_does_not_deadlock_a_small_pool():
    items = [("c", 0), ("b", 0), ("a", 0), ("a", 1), ("a", 2)]
    log, _, _ = _schedule(items, {"b": ["a"], "c": ["b"]}, workers=2, hold=0.01)
    starts = [x[0] for kind, x in log if kind == "start"]
    assert starts.index("c") > starts.index("b") > max(i for i, k in enumerate(starts) if k == "a")


def test_default_jobs():
    gib = 1024**3
    assert ci.default_jobs(12, 18, 100 * gib)[0] == 4      # 18 cores // 4
    assert ci.default_jobs(2, 18, 100 * gib)[0] == 2       # never more than the jobs
    assert ci.default_jobs(12, 18, 9 * gib)[0] == 2        # 9 GiB free / 4 GiB a job
    assert ci.default_jobs(12, 2, None)[0] == 1            # at least one
    assert ci.serial_reason("abstractcore", _job_id("local-models"))
    assert ci.serial_reason("abstractcore", _job_id("test")) is None
    assert ci.serial_reason("abstractframework", _job_id("bootstrap-smoke"))  # one port 18080 on this Mac


def _job_id(job_id):
    return ci.Job("CI", "ci.yml", {}, job_id, {}, {}, f"ci/{job_id}")


def test_light_tier_selects_tests_that_change_name_or_import_the_changed_modules():
    files = ["src/pkg/model_host.py", "src/pkg/cli.py", "src/pkg/util.py", "tests/test_model_host.py",
             "tests/test_model_host_portable.py", "tests/test_entry.py", "tests/test_other.py", "tests/fakes.py",
             "tests/test_uses_fakes.py", "docs/a.md"]
    texts = {
        "tests/test_entry.py": "from pkg import (\n    cli,\n    other,\n)\n",
        "tests/test_other.py": "import pkg.util as u\n",
        "tests/test_uses_fakes.py": "from fakes import FakeHost\n",
    }
    read = lambda path: texts.get(path, "")
    keep, uncovered, _ = ci.light_tests(["docs/a.md"], files, read)
    assert keep == {} and uncovered == []
    keep, uncovered, _ = ci.light_tests(["src/pkg/model_host.py"], files, read)
    assert sorted(keep) == ["tests/test_model_host.py", "tests/test_model_host_portable.py"]
    assert keep["tests/test_model_host.py"] == ["named after src/pkg/model_host.py"]
    keep, _, _ = ci.light_tests(["src/pkg/cli.py", "src/pkg/util.py"], files, read)
    assert keep == {"tests/test_entry.py": ["imports pkg.cli"], "tests/test_other.py": ["imports pkg.util"]}
    keep, _, _ = ci.light_tests(["tests/test_other.py"], files, read)
    assert keep == {"tests/test_other.py": ["changed"]}
    keep, uncovered, _ = ci.light_tests(["tests/fakes.py"], files, read)
    assert list(keep) == ["tests/test_uses_fakes.py"] and uncovered == []
    assert ci.light_tests(["tests/conftest.py"], files, read) == (None, [], [])
    assert ci.light_tests(["pyproject.toml"], files, read) == (None, [], [])


def test_light_tier_fails_loud_when_a_changed_module_has_no_test():
    files = ["src/pkg/lonely.py", "tests/test_x.py"]
    keep, uncovered, _ = ci.light_tests(["src/pkg/lonely.py"], files, lambda p: "import os\n")
    assert keep == {} and uncovered == ["src/pkg/lonely.py"]


def test_light_tier_covers_every_changed_file_not_only_python():
    files = ["src/pkg/assets/model_catalog.yaml", "src/pkg/console/static/app.js", "scripts/deploy.sh",
             "tests/test_model_catalog.py", "tests/test_console_app.py", "tests/fixtures/rows.json",
             "web/package.json", "web/src/view.ts", "README.md"]
    read = lambda path: ""
    # A catalog entry (ADR 0051's own light example) keeps the test named after it.
    keep, uncovered, _ = ci.light_tests(["src/pkg/assets/model_catalog.yaml"], files, read)
    assert keep == {"tests/test_model_catalog.py": ["named after src/pkg/assets/model_catalog.yaml"]}
    # Static JS and a shell script with no test of that name are uncovered: a red light run.
    keep, uncovered, _ = ci.light_tests(["src/pkg/console/static/app.js", "scripts/deploy.sh"], files, read)
    assert "src/pkg/console/static/app.js" not in uncovered  # test_console_app holds "app"
    assert uncovered == ["scripts/deploy.sh"]
    # A fixture under tests/ runs the whole suite.
    assert ci.light_tests(["tests/fixtures/rows.json"], files, read) == (None, [], [])
    # A file an npm package owns is left to the narrowed npm step, not to pytest.
    keep, uncovered, owned = ci.light_tests(["web/src/view.ts"], files, read)
    assert keep == {} and uncovered == [] and owned == ["web/src/view.ts"]
    # Documentation needs no test.
    assert ci.light_tests(["README.md"], files, read) == ({}, [], [])


def test_a_documentation_only_change_is_the_one_light_run_without_tests():
    assert ci.docs_only(["README.md", "CHANGELOG.md", "llms-full.txt"])
    assert not ci.docs_only(["README.md", "src/pkg/catalog.json"])
    assert not ci.docs_only([])  # no change at all is not a documentation change


def test_a_light_run_that_executed_no_test_is_red(tmp_path):
    counts = tmp_path / "light-counts"
    assert ci.light_executed(counts) == 0           # nothing ran at all
    counts.write_text("0\n0\n", encoding="utf-8")
    assert ci.light_executed(counts) == 0           # every pytest kept nothing
    counts.write_text("0\n3\n", encoding="utf-8")
    assert ci.light_executed(counts) == 3


def test_module_names_and_imports():
    assert ci.module_name("src/abstractgateway/model_host.py") == "abstractgateway.model_host"
    assert ci.module_name("abstractcore/providers/__init__.py") == "abstractcore.providers"
    assert ci.imports_module("from abstractcore.providers.mlx import X\n", "abstractcore.providers.mlx")
    assert not ci.imports_module("from abstractcore.providers.mlx_native import X\n", "abstractcore.providers.mlx")
    assert ci.imports_module("    from abstractcore.providers import mlx, hf\n", "abstractcore.providers.mlx")


def test_light_steps_narrow_npm_and_cargo(tmp_path):
    import json

    web = tmp_path / "web"
    (web / "src").mkdir(parents=True)
    (web / "src" / "a.ts").write_text("", encoding="utf-8")
    (web / "package.json").write_text(json.dumps({"scripts": {"test": "vitest run"}}), encoding="utf-8")
    script, note = ci.light_step("npm test", "web", web, ["web/src/a.ts", "README.md"])
    assert script == f"npx vitest related --run {web / 'src' / 'a.ts'}" and "vitest related" in note
    assert ci.light_step("npm test", "web", web, ["README.md"])[0] is None

    mono = tmp_path / "mono"
    mono.mkdir()
    (mono / "package.json").write_text(json.dumps({"workspaces": ["ui-kit", "panel-chat"],
                                                   "scripts": {"test": "npm --workspaces run test"}}), encoding="utf-8")
    assert ci.light_step("npm test", ".", mono, ["ui-kit/src/x.ts"])[0] == "npm --workspace ui-kit --if-present run test"
    assert ci.light_step("npm test", ".", mono, ["scripts/check.mjs"])[0] == "npm test"
    assert ci.light_step("npm test", ".", mono, ["CHANGELOG.md", "llms-full.txt", "ui-kit/src/x.ts"])[0] == \
        "npm --workspace ui-kit --if-present run test"

    ws = tmp_path / "rust"
    (ws / "tui").mkdir(parents=True)
    (ws / "Cargo.toml").write_text('[workspace]\nmembers = ["tui", "core"]\n', encoding="utf-8")
    (ws / "tui" / "Cargo.toml").write_text('[package]\nname = "abstractcode"\n', encoding="utf-8")
    assert ci.light_step("cargo test --workspace --locked", ".", ws, ["tui/src/main.rs"])[0] == \
        "cargo test -p abstractcode --locked"
    assert ci.light_step("cargo test --locked", "console-tui", tmp_path, ["src/x.py"])[0] is None
    assert ci.light_step("python -m pytest", ".", tmp_path, ["a.py"]) == ("python -m pytest", "")


def test_light_tier_keeps_one_python_per_matrix():
    group = [ci.Job("CI", "ci.yml", {}, "test", {}, {"python-version": v}, f"ci/test ({v})", python=v)
             for v in ("3.10", "3.11", "3.12", "3.13")]
    assert [j.python for j in ci.light_matrix(group)] == ["3.10", "3.11", "3.13"]
    os_matrix = [ci.Job("CI", "ci.yml", {}, "smoke", {}, {"os": o}, f"ci/smoke ({o})") for o in ("ubuntu", "macos")]
    assert [j.matrix["os"] for j in ci.light_matrix(os_matrix)] == ["macos"]
    assert ci.light_matrix(group[:1]) == []


def test_light_plugin_narrows_the_top_level_pytest_only(tmp_path):
    import json
    import os
    import subprocess

    (tmp_path / "plugin").mkdir()
    (tmp_path / "plugin" / "ci_local_light.py").write_text(ci.LIGHT_PLUGIN, encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
    (tmp_path / "tests" / "test_b.py").write_text("def test_b():\n    raise AssertionError\n", encoding="utf-8")

    counts = tmp_path / "counts"

    def run(selected):
        env = {**os.environ, "PYTHONPATH": str(tmp_path / "plugin"), "PYTEST_ADDOPTS": "-p ci_local_light",
               "CI_LOCAL_LIGHT_TESTS": json.dumps(selected), "CI_LOCAL_LIGHT_ROOT": str(tmp_path),
               "CI_LOCAL_LIGHT_COUNTS": str(counts)}
        return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
                              cwd=tmp_path, env=env, capture_output=True, text=True)

    out = run(["tests/test_a.py"])
    assert out.returncode == 0 and "1 passed, 1 deselected" in out.stdout, out.stdout
    out = run([])
    assert out.returncode == 0, out.stdout  # nothing selected is not "no tests collected"
    assert run(["tests/test_b.py"]).returncode == 1
    assert counts.read_text(encoding="utf-8").split() == ["1", "0", "1"]  # what the run-level check sums


def _cargo_target(path: Path) -> Path:
    (path / "release" / "deps").mkdir(parents=True)
    (path / "CACHEDIR.TAG").write_text("Signature: 8a477f597d28d172789f06886806bc55\n"
                                       "# This file is a cache directory tag created by cargo.\n", encoding="utf-8")
    binary = path / "release" / "abstracttui"
    binary.write_text("binary", encoding="utf-8")
    binary.chmod(0o755)
    (path / "release" / "abstracttui.d").write_text("deps", encoding="utf-8")
    (path / "release" / "deps" / "libbig.rlib").write_text("x" * 1000, encoding="utf-8")
    return path


def test_a_finished_job_keeps_its_executables_not_its_rust_build_folder(tmp_path):
    run = tmp_path / "run"
    job = run / "jobs" / "01-ci-tui"
    target = _cargo_target(job / "work" / "abstracttui" / "target")
    other = job / "work" / "abstracttui" / "web" / "target"  # a folder named target that cargo did not make
    other.mkdir(parents=True)
    (other / "keep.txt").write_text("x", encoding="utf-8")
    notes = ci.clean_rust_builds(job, run)
    assert not target.exists() and other.exists()
    assert (job / "rust-binaries" / "release" / "abstracttui").read_text(encoding="utf-8") == "binary"
    assert not (job / "rust-binaries" / "release" / "abstracttui.d").exists()
    assert len(notes) == 1 and "removed the Rust build folder" in notes[0]
    assert ci.clean_rust_builds(job, run) == []  # nothing left to remove


def test_the_repository_name_comes_from_origin_not_the_folder():
    for url in ("https://github.com/lpalbou/AbstractFramework.git", "git@github.com:lpalbou/AbstractFramework.git",
                "https://github.com/lpalbou/AbstractFramework", "https://github.com/lpalbou/AbstractFramework/",
                "ssh://git@github.com/lpalbou/AbstractFramework.git"):
        assert ci.repo_name_from(url, "wt-root") == "abstractframework", url
    assert ci.repo_name_from("/Users/me/src/AbstractGateway", "wt-w5-timing") == "abstractgateway"
    assert ci.repo_name_from("", "wt-w3-ttl") == "wt-w3-ttl"  # no origin: the folder name


def test_a_worktree_run_gets_the_main_checkouts_name(tmp_path):
    import subprocess

    wt = tmp_path / "untracked" / "wt-w3-ttl"
    wt.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(wt)], check=True)
    subprocess.run(["git", "-C", str(wt), "remote", "add", "origin", "https://github.com/lpalbou/AbstractCore.git"], check=True)
    runner = ci.Runner(ci.build_parser().parse_args(["x"]), wt, tmp_path)
    assert runner.repo_name == "abstractcore"
    assert ci.serial_reason(runner.repo_name, _job_id("local-models"))  # the serial rule follows the name


def test_rust_builds_share_one_folder_per_repository_outside_the_run():
    assert ci.cargo_target_dir("abstractcore") == Path.home() / "Library" / "Caches" / "ci-gate" / "cargo-target" / "abstractcore"
    assert ci.cargo_target_dir("abstractcore") != ci.cargo_target_dir("abstracttui")


def _runs(root: Path, repo: str, stamps: list[str]) -> list[Path]:
    out = []
    for stamp in stamps:
        d = root / f"{repo}-{stamp}-0123abcd"
        (d / "jobs").mkdir(parents=True)
        (d / ci.RUN_LOCK).write_text("", encoding="utf-8")
        out.append(d)
    return out


def test_keep_runs_deletes_the_oldest_runs_of_the_same_repository_only(tmp_path):
    root = tmp_path / "ci-gate" / "runs"
    old1, old2, old3, mid, current = _runs(root, "abstractcore", [
        "20261101-090000", "20261101-100000", "20261102-090000", "20261103-090000", "20261103-100000"])
    (neighbour,) = _runs(root, "abstractcore-tui", ["20261101-080000"])  # another repository, same prefix
    deleted, note = ci.prune_runs(root, "abstractcore", current, 3, tmp_path / "ci-gate")
    assert sorted(deleted) == [old1, old2] and note == ""  # three remain, this run included
    assert old3.exists() and mid.exists() and current.exists() and neighbour.exists()
    # 0 (or 'all') keeps every run folder.
    assert ci.prune_runs(root, "abstractcore", current, 0, tmp_path / "ci-gate") == ([], "")
    assert ci.parse_keep_runs("all") == 0 and ci.parse_keep_runs("3") == 3
    with pytest.raises(Exception):
        ci.parse_keep_runs("-1")


def test_keep_runs_never_deletes_a_run_in_progress_or_outside_the_gate_cache(tmp_path):
    import fcntl

    root = tmp_path / "ci-gate" / "runs"
    busy, idle, current = _runs(root, "abstractcore", ["20261101-090000", "20261101-100000", "20261103-100000"])
    with open(busy / ci.RUN_LOCK, "w", encoding="utf-8") as held:
        fcntl.flock(held, fcntl.LOCK_EX)  # another gate is running in this folder
        deleted, note = ci.prune_runs(root, "abstractcore", current, 1, tmp_path / "ci-gate")
    assert deleted == [idle] and busy.exists() and busy.name in note
    # An older gate's folder (no lock) whose job log just changed is still running.
    legacy = root / "abstractcore-20261101-080000-0123abcd"
    (legacy / "jobs" / "01-x").mkdir(parents=True)
    (legacy / "jobs" / "01-x" / "log.txt").write_text("running", encoding="utf-8")
    deleted, _ = ci.prune_runs(root, "abstractcore", current, 1, tmp_path / "ci-gate")
    assert legacy.exists() and deleted == [busy]
    # A runs root outside the gate's cache is refused: nothing deleted.
    elsewhere = tmp_path / "scratch" / "runs"
    a, b = _runs(elsewhere, "abstractcore", ["20261101-090000", "20261103-100000"])
    deleted, note = ci.prune_runs(elsewhere, "abstractcore", b, 1, tmp_path / "ci-gate")
    assert deleted == [] and a.exists() and "not under" in note
