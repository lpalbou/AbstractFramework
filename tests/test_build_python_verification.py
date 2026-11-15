"""The local build fails on a broken dependency of the framework, and only on that.

`scripts/build.sh` ends its Python phase with a dependency check and an import check. The
dependency check covers what the build installed: each local package with the profile's
extras, and everything those depend on. Three other things are shown and never fail the
build: a release pin of the root package that a checkout moved past, and a conflict between
unrelated tools that happen to live in the same environment.
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
        (info / 'direct_url.json').write_text(direct_url if isinstance(direct_url, str) else json.dumps(direct_url))


def _function(name):
    match = re.search(rf'^{name}\(\) \{{\n.*?^\}}', BUILD_SH, re.M | re.S)
    assert match, f'{name} is missing from scripts/build.sh'
    return match.group(0)


def _run_verification(bindir, extras='', roots=('abstractcore',), meta='', replaced=''):
    """The script's own Verification block and checker, with the package inventory stubbed.

    roots: the local Python packages; meta: the root package; replaced: a root whose
    checkout pip no longer serves.
    """
    start = BUILD_SH.index('    section "Python — Verification"')
    end = BUILD_SH.index('\n# ═', start)
    verification = BUILD_SH[start:end]  # includes the closing main Python-selection `fi`
    names = list(roots) + ([meta] if meta else [])
    command = '''
section() { :; }
ok_line() { echo "ok: $*"; }
warn_line() { echo "$*"; }
info_line() { echo "$*"; }
AF_PKG_ID=(''' + ' '.join(names) + ''')
af_pkg_indices() {
    local i=0
    while [ $i -lt ''' + str(len(roots)) + ''' ]; do [ "$1" = python ] && echo $i; i=$((i + 1)); done
    if [ "$1" = meta ] && [ -n "$FIXTURE_META" ]; then echo ''' + str(len(roots)) + '''; fi
    return 0
}
af_pkg_location() { echo "${AF_PKG_ID[$1]}"; }
build_profile_extras() { printf '%s' "$FIXTURE_EXTRAS"; }
editable_dist_name() { [ "${1##*/}" = "$FIXTURE_REPLACED" ] || echo "${1##*/}"; }
ROOT_DIR=/fixture/workspace
PYTHON_BUILD_PROFILE=fixture
C_RED='' C_RESET=''
''' + _function('dependency_problems') + '''
if true; then
''' + verification + '\nif $py_ok; then exit 0; else exit 1; fi\n'
    env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ.get('PATH', ''),
               PIP_DISABLE_PIP_VERSION_CHECK='1', FIXTURE_EXTRAS=extras, FIXTURE_META=meta,
               FIXTURE_REPLACED=replaced)
    return subprocess.run(['bash', '-c', command], env=env, capture_output=True, text=True)


def _framework_package(site, name='abstractcore', requires=('af-build-fixture-b>=2',), extras=(), imports_ok=True):
    """One local package: its metadata, and a real module the import check can load."""
    _dist(site, name, '1.0', requires=requires, extras=extras)
    body = 'create_llm = object()\n' if imports_ok else 'raise ImportError("fixture import failure")\n'
    (site / f'{name}.py').write_text(body)


def test_a_satisfied_graph_with_working_imports_passes(isolated_python):
    bindir, site = isolated_python
    _framework_package(site)
    _dist(site, 'af-build-fixture-b', '2.0')
    result = _run_verification(bindir)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'ok: Every dependency of the local packages is satisfied' in result.stdout


def test_an_unmet_requirement_of_a_local_package_fails_the_build(isolated_python):
    bindir, site = isolated_python
    _framework_package(site)
    _dist(site, 'af-build-fixture-b', '1.0')
    result = _run_verification(bindir)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'abstractcore 1.0 requires af-build-fixture-b>=2, but af-build-fixture-b 1.0 is installed' in result.stdout


def test_every_local_package_is_checked_not_only_the_first(isolated_python):
    bindir, site = isolated_python
    _framework_package(site)
    _framework_package(site, name='abstractruntime', requires=['af-build-fixture-c>=1'])
    _dist(site, 'af-build-fixture-b', '2.0')
    result = _run_verification(bindir, roots=('abstractcore', 'abstractruntime'))
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'abstractruntime 1.0 requires af-build-fixture-c, which is not installed' in result.stdout


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


def test_an_extra_the_package_does_not_declare_fails_the_build(isolated_python):
    """pip only warns about an unknown extra and installs nothing for it."""
    bindir, site = isolated_python
    _framework_package(site, extras=['apple'])
    _dist(site, 'af-build-fixture-b', '2.0')
    result = _run_verification(bindir, extras='[all-apple]')
    assert result.returncode == 1, result.stdout + result.stderr
    assert "abstractcore 1.0 does not declare the extra 'all-apple' this build asks for" in result.stdout


def test_a_requirement_that_cannot_be_read_is_named_not_a_traceback(isolated_python):
    bindir, site = isolated_python
    _framework_package(site, requires=['af-build-fixture-b>=2', 'af-build-fixture-c>=1.17.*'])
    _dist(site, 'af-build-fixture-b', '2.0')
    result = _run_verification(bindir)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'abstractcore 1.0 has a requirement that cannot be read (af-build-fixture-c>=1.17.*)' in result.stdout
    assert 'Traceback' not in result.stdout + result.stderr


def test_a_checkout_pip_replaced_with_a_release_fails_the_build(isolated_python):
    """The build would otherwise run released code and still say "editable"."""
    bindir, site = isolated_python
    _framework_package(site)
    _dist(site, 'af-build-fixture-b', '2.0')
    result = _run_verification(bindir, replaced='abstractcore')
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'abstractcore is not installed from its checkout (abstractcore): pip replaced it with a released version' in result.stdout


def test_a_release_pin_a_checkout_moved_past_is_shown_and_does_not_fail_the_build(isolated_python):
    """Between two releases a checkout is normally ahead of the root package's pin."""
    bindir, site = isolated_python
    _framework_package(site)
    _dist(site, 'af-build-fixture-b', '2.0')
    _dist(site, 'abstractframework', '9.9', requires=['abstractcore==0.9'])
    result = _run_verification(bindir, meta='abstractframework')
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'the pins must match before a release' in result.stdout
    assert 'abstractframework 9.9 requires abstractcore==0.9, but abstractcore 1.0 is installed' in result.stdout


def test_a_conflict_between_unrelated_tools_is_shown_and_does_not_fail_the_build(isolated_python):
    """A publishing tool in a long-lived environment once blocked every local start."""
    bindir, site = isolated_python
    _framework_package(site)
    _dist(site, 'af-build-fixture-b', '2.0')
    _dist(site, 'af-build-fixture-tool', '7.0', requires=['af-build-fixture-b>=3'])
    result = _run_verification(bindir)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'af-build-fixture-tool 7.0 has requirement af-build-fixture-b>=3' in result.stdout
    assert 'The local packages do not depend on any of it' in result.stdout


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


def test_the_final_summary_repeats_what_is_not_satisfied():
    """The verification scrolls away behind the npm and Rust output; the summary is what is read."""
    start = BUILD_SH.index('printf "  ${C_BOLD}Build complete.${C_RESET}\\n"')
    end = BUILD_SH.index('# Exit non-zero when any selected ecosystem failed', start)
    command = '''
C_RED='' C_GREEN='' C_BOLD='' C_RESET='' C_DIM='' C_YELLOW=''
BUILD_PYTHON=true BUILD_NPM=false BUILD_RUST=false py_ok=false VENV_DIR=/fixture AF_BUILD_WRAPPER=1
_dependency_report="abstractcore 1.0 requires af-build-fixture-b>=2, but af-build-fixture-b 1.0 is installed"
''' + BUILD_SH[start:end]
    result = subprocess.run(['bash', '-c', command], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    failed, repeated = result.stdout.index('FAILED:'), result.stdout.index('abstractcore 1.0 requires af-build-fixture-b>=2')
    assert failed < repeated


_INSTALL_STUBS = '''
set -euo pipefail
require_repo() { :; }
package_line() { :; }
dim_line() { :; }
section() { :; }
af_die() { echo "died: $*"; exit 1; }
explain_resolution_failure() { echo "explain: $*"; }
editable_dist_name() { echo "Dist-${1##*/}"; }
pip() { printf '%s\\n' "$*" >> "$PIP_LOG"; }
PY_DEPENDENCY_SPECS=()
'''


def _install_functions():
    return _function('install_editable') + '\n' + _function('install_python_dependencies') + '\n'


def _run_install(tmp_path, body, stubs=_INSTALL_STUBS, shell='bash'):
    log = tmp_path / 'pip.log'
    env = dict(os.environ, ROOT_DIR=str(tmp_path), PIP_LOG=str(log))
    result = subprocess.run([shell, '-c', stubs + _install_functions() + body], env=env,
                            capture_output=True, text=True)
    return result, (log.read_text().splitlines() if log.exists() else [])


def test_dependencies_are_installed_together_and_with_build_isolation(tmp_path):
    """Each checkout goes in without its dependencies; those are then installed in ONE pip run.

    One run, because package by package pip takes the newest pandas for the first packages
    before it has seen the package that needs pandas<3, and on a new machine it then failed
    with resolution-too-deep after three hours. By name and WITH build isolation, because a
    dependency PyPI ships only as source brings its own build backend.
    """
    result, calls = _run_install(tmp_path, '''
install_editable one "[apple]" "pip t0" ""
install_editable two "" "pip t1" "one"
install_python_dependencies
''')
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(calls) == 3, calls  # two checkouts, then ONE run for the dependencies of both
    first, second, dependencies = calls
    for local, name in ((first, 'one'), (second, 'two')):
        assert '--no-build-isolation' in local.split() and '--no-deps' in local.split()
        assert local.endswith(f'-e {tmp_path}/{name}'), local
    assert dependencies.endswith(' Dist-one[apple] Dist-two'), dependencies
    assert '--no-build-isolation' not in dependencies.split()
    assert '-e' not in dependencies.split() and '--no-deps' not in dependencies.split()


def test_a_dependency_install_that_fails_stops_the_build_and_names_the_packages(tmp_path):
    stubs = _INSTALL_STUBS.replace(
        '''pip() { printf '%s\\n' "$*" >> "$PIP_LOG"; }''',
        '''pip() { case " $* " in *" -e "*) return 0 ;; *) return 1 ;; esac; }''')
    assert stubs != _INSTALL_STUBS
    result, _ = _run_install(tmp_path, '''
install_editable one "[apple]" "pip t0" ""
install_editable two "" "pip t1" "one"
install_python_dependencies
echo "the build went on"
''', stubs=stubs)
    assert result.returncode == 1
    assert 'explain: Dist-one[apple] Dist-two' in result.stdout
    assert 'died: pip could not install the dependencies of the local packages (Dist-one[apple] Dist-two)' in result.stdout
    assert 'the build went on' not in result.stdout


def test_a_build_with_no_local_python_package_installs_no_dependencies(tmp_path):
    """Under `set -u`, the bash that ships with macOS (3.2) rejects an empty array expansion."""
    shell = '/bin/bash' if Path('/bin/bash').exists() else 'bash'
    result, calls = _run_install(tmp_path, 'install_python_dependencies\necho reached\n', shell=shell)
    assert result.returncode == 0, result.stdout + result.stderr
    assert calls == [] and 'reached' in result.stdout


def test_the_build_installs_checkouts_then_their_dependencies_then_the_meta_package(tmp_path):
    """The order in the script itself: the dependencies of all checkouts before the root package."""
    start = BUILD_SH.index('    # ── Every Python package, tier by tier (scripts/lib/packages.txt) ──')
    marker = '    done < <(af_pkg_indices meta)\n'
    end = BUILD_SH.index(marker, start) + len(marker)
    result, calls = _run_install(tmp_path, '''
AF_PKG_ID=(one two abstractframework)
AF_PKG_TIER=(0 1 2)
af_pkg_indices() { if [ "$1" = python ]; then echo 0; echo 1; else echo 2; fi; }
af_tier_title() { echo "Tier $1"; }
af_pkg_location() { echo "${AF_PKG_ID[$1]}"; }
af_pkg_dep_ids() { echo ""; }
build_profile_extras() { if [ "$1" = one ]; then printf '%s' "[$2]"; fi; }
PYTHON_BUILD_PROFILE=apple
''' + BUILD_SH[start:end])
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(calls) == 4, calls
    assert calls[0].endswith(f'--no-deps -e {tmp_path}/one') and calls[1].endswith(f'--no-deps -e {tmp_path}/two')
    assert calls[2].endswith(' Dist-one[apple] Dist-two') and '--no-deps' not in calls[2].split()
    assert calls[3].endswith(f'--no-deps -e {tmp_path}'), calls[3]


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
    (tmp_path / 'link with space').symlink_to(tmp_path / 'checkout', target_is_directory=True)
    _dist(site, 'AbstractRuntime', '1.0', direct_url={'url': package.resolve().as_uri(), 'dir_info': {'editable': True}})
    _dist(site, 'af-build-fixture-b', '2.0')
    _dist(site, 'af-build-fixture-damaged', '1.0', direct_url='{not json')
    command = _function('editable_dist_name') + '\neditable_dist_name "$1"\n'
    env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ.get('PATH', ''))

    def name_of(path):
        found = subprocess.run(['bash', '-c', command, 'name', str(path)], env=env, capture_output=True, text=True)
        assert found.returncode == 0, found.stdout + found.stderr
        return found.stdout.strip()

    assert name_of(package) == 'AbstractRuntime'
    # The workspace is often reached through a symlink (/tmp on a Mac); pip recorded the real path.
    assert name_of(tmp_path / 'link with space' / 'abstractruntime') == 'AbstractRuntime'
    assert name_of(tmp_path / 'checkout') == ''
