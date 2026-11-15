"""The local build fails on a broken dependency of the framework, and only on that.

`scripts/build.sh` ends its Python phase with a dependency check and an import check. The
dependency check covers what the build installed: each local package with the profile's
extras, and everything those depend on. A conflict between unrelated tools that happen to
live in the same environment is shown and never fails the build.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import venv

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD_SH = (ROOT / 'scripts/build.sh').read_text()


@pytest.fixture
def isolated_python(tmp_path):
    env = tmp_path / 'venv'
    venv.EnvBuilder(with_pip=True).create(env)
    bindir = env / ('Scripts' if os.name == 'nt' else 'bin')
    python = bindir / ('python.exe' if os.name == 'nt' else 'python')
    site = Path(subprocess.check_output([str(python), '-c',
        'import sysconfig; print(sysconfig.get_paths()["purelib"])'], text=True).strip())
    return bindir, site


def _dist(site, name, version, requires=(), extras=(), direct_url=None):
    info = site / f"{name.replace('-', '_')}-{version}.dist-info"
    info.mkdir()
    lines = ['Metadata-Version: 2.1', f'Name: {name}', f'Version: {version}']
    lines += [f'Provides-Extra: {extra}' for extra in extras]
    lines += [f'Requires-Dist: {requirement}' for requirement in requires]
    (info / 'METADATA').write_text('\n'.join(lines) + '\n')
    if direct_url is not None:
        (info / 'direct_url.json').write_text(json.dumps(direct_url))


def _function(name):
    match = re.search(rf'^{name}\(\) \{{\n.*?^\}}', BUILD_SH, re.M | re.S)
    assert match, f'{name} is missing from scripts/build.sh'
    return match.group(0)


def _run_verification(bindir, extras=''):
    start = BUILD_SH.index('    section "Python — Verification"')
    end = BUILD_SH.index('\n# ═', start)
    verification = BUILD_SH[start:end]  # includes the closing main Python-selection `fi`
    command = '''
section() { :; }
ok_line() { :; }
warn_line() { echo "$*"; }
info_line() { echo "$*"; }
af_pkg_indices() { echo 0; }
build_profile_extras() { printf '%s' "$FIXTURE_EXTRAS"; }
AF_PKG_ID=(abstractcore)
PYTHON_BUILD_PROFILE=fixture
C_RED='' C_RESET=''
if true; then
''' + verification + '\nif $py_ok; then exit 0; else exit 1; fi\n'
    env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ.get('PATH', ''),
               PIP_DISABLE_PIP_VERSION_CHECK='1', FIXTURE_EXTRAS=extras)
    return subprocess.run(['bash', '-c', command], env=env, capture_output=True, text=True)


def _framework_package(site, requires=('af-build-fixture-b>=2',), extras=(), imports_ok=True):
    """One local package: its metadata, and a real module the import check can load."""
    _dist(site, 'abstractcore', '1.0', requires=requires, extras=extras)
    (site / 'abstractcore.py').write_text(
        'create_llm = object()\n' if imports_ok else 'raise ImportError("fixture import failure")\n')


def test_a_satisfied_graph_with_working_imports_passes(isolated_python):
    bindir, site = isolated_python
    _framework_package(site)
    _dist(site, 'af-build-fixture-b', '2.0')
    result = _run_verification(bindir)
    assert result.returncode == 0, result.stdout + result.stderr


def test_an_unmet_requirement_of_a_local_package_fails_the_build(isolated_python):
    bindir, site = isolated_python
    _framework_package(site)
    _dist(site, 'af-build-fixture-b', '1.0')
    result = _run_verification(bindir)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'abstractcore 1.0 requires af-build-fixture-b>=2, but af-build-fixture-b 1.0 is installed' in result.stdout


def test_an_unmet_requirement_deeper_in_the_graph_fails_the_build(isolated_python):
    bindir, site = isolated_python
    _framework_package(site)
    _dist(site, 'af-build-fixture-b', '2.0', requires=['af-build-fixture-c>=5'])
    _dist(site, 'af-build-fixture-c', '1.0')
    result = _run_verification(bindir)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'af-build-fixture-b 2.0 requires af-build-fixture-c>=5' in result.stdout


def test_a_missing_dependency_of_a_requested_extra_fails_the_build(isolated_python):
    bindir, site = isolated_python
    _framework_package(site, requires=['af-build-fixture-b>=2', 'af-build-fixture-c>=1; extra == "apple"'],
                       extras=['apple'])
    _dist(site, 'af-build-fixture-b', '2.0')
    result = _run_verification(bindir, extras='[apple]')
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'abstractcore 1.0 requires af-build-fixture-c, which is not installed' in result.stdout


def test_an_extra_the_build_did_not_request_is_not_checked(isolated_python):
    bindir, site = isolated_python
    _framework_package(site, requires=['af-build-fixture-b>=2', 'af-build-fixture-c>=1; extra == "apple"'],
                       extras=['apple'])
    _dist(site, 'af-build-fixture-b', '2.0')
    result = _run_verification(bindir, extras='')
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_conflict_between_unrelated_tools_is_shown_and_does_not_fail_the_build(isolated_python):
    """A publishing tool in a long-lived environment once blocked every local start."""
    bindir, site = isolated_python
    _framework_package(site)
    _dist(site, 'af-build-fixture-b', '2.0')
    _dist(site, 'af-build-fixture-tool', '7.0', requires=['af-build-fixture-b>=3'])
    result = _run_verification(bindir)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'af-build-fixture-tool 7.0 has requirement af-build-fixture-b>=3' in result.stdout
    assert 'does not depend on them' in result.stdout


def test_a_failing_import_fails_the_build(isolated_python):
    bindir, site = isolated_python
    _framework_package(site, imports_ok=False)
    _dist(site, 'af-build-fixture-b', '2.0')
    result = _run_verification(bindir)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'Some imports failed' in result.stdout


def test_a_local_package_that_is_not_installed_fails_the_build(isolated_python):
    bindir, site = isolated_python
    (site / 'abstractcore.py').write_text('create_llm = object()\n')
    result = _run_verification(bindir)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'abstractcore is not installed' in result.stdout


def test_dependencies_are_installed_with_build_isolation(tmp_path):
    """A dependency PyPI ships only as source brings its own build backend.

    The local package is installed without its dependencies and without build isolation;
    its dependencies are then installed by name, WITH isolation. One command for both
    failed on every machine whose pip cache held no prebuilt wheel of that dependency.
    """
    log = tmp_path / 'pip.log'
    command = '''
require_repo() { :; }
package_line() { :; }
dim_line() { :; }
explain_resolution_failure() { :; }
af_die() { echo "died: $*"; exit 1; }
editable_dist_name() { echo "Fixture-Dist"; }
pip() { printf '%s\\n' "$*" >> "$PIP_LOG"; }
''' + _function('install_editable') + '\ninstall_editable pkg "[apple]" "pip t0" ""\n'
    env = dict(os.environ, ROOT_DIR=str(tmp_path), PIP_LOG=str(log))
    result = subprocess.run(['bash', '-c', command], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    local, dependencies = log.read_text().splitlines()
    assert '--no-build-isolation' in local.split() and '--no-deps' in local.split()
    assert local.endswith(f'-e {tmp_path}/pkg'), local
    assert dependencies.endswith(' Fixture-Dist[apple]'), dependencies
    assert '--no-build-isolation' not in dependencies.split()
    assert '-e' not in dependencies.split() and '--no-deps' not in dependencies.split()


def test_an_editable_install_pip_did_not_record_stops_the_build(tmp_path):
    command = '''
require_repo() { :; }
package_line() { :; }
dim_line() { :; }
explain_resolution_failure() { :; }
af_die() { echo "died: $*"; exit 1; }
editable_dist_name() { :; }
pip() { :; }
''' + _function('install_editable') + '\ninstall_editable pkg "" "pip t0" ""\n'
    result = subprocess.run(['bash', '-c', command], env=dict(os.environ, ROOT_DIR=str(tmp_path)),
                            capture_output=True, text=True)
    assert result.returncode == 1
    assert 'died: pip recorded no editable install for pkg' in result.stdout


def test_the_published_name_of_an_editable_install_is_read_from_pip(isolated_python, tmp_path):
    bindir, site = isolated_python
    package = tmp_path / 'checkout' / 'abstractruntime'
    package.mkdir(parents=True)
    _dist(site, 'AbstractRuntime', '1.0', direct_url={'url': package.resolve().as_uri(), 'dir_info': {'editable': True}})
    _dist(site, 'af-build-fixture-b', '2.0')
    command = _function('editable_dist_name') + '\neditable_dist_name "$1"\n'
    env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ.get('PATH', ''))
    found = subprocess.run(['bash', '-c', command, 'name', str(package)], env=env, capture_output=True, text=True)
    assert found.returncode == 0 and found.stdout.strip() == 'AbstractRuntime', found.stdout + found.stderr
    other = subprocess.run(['bash', '-c', command, 'name', str(tmp_path / 'checkout')], env=env, capture_output=True, text=True)
    assert other.returncode == 0 and other.stdout.strip() == '', other.stdout + other.stderr
