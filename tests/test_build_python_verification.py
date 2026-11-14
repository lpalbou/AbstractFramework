"""The local build rejects a broken final dependency graph even when imports work."""
import os
from pathlib import Path
import subprocess
import venv

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_python(tmp_path):
    env = tmp_path / 'venv'
    venv.EnvBuilder(with_pip=True).create(env)
    bindir = env / ('Scripts' if os.name == 'nt' else 'bin')
    python = bindir / ('python.exe' if os.name == 'nt' else 'python')
    site = Path(subprocess.check_output([str(python), '-c',
        'import sysconfig; print(sysconfig.get_paths()["purelib"])'], text=True).strip())
    return bindir, site


@pytest.mark.parametrize('compatible,imports_ok,expected', [(True, True, 0), (False, True, 1), (True, False, 1)])
def test_final_python_verification_checks_dependencies_and_imports(isolated_python, tmp_path, compatible, imports_ok, expected):
    bindir, site = isolated_python
    a = site / 'af_build_fixture_a-1.0.dist-info'
    a.mkdir()
    (a / 'METADATA').write_text('Metadata-Version: 2.1\nName: af-build-fixture-a\nVersion: 1.0\nRequires-Dist: af-build-fixture-b>=2\n')
    version = '2.0' if compatible else '1.0'
    b = site / f'af_build_fixture_b-{version}.dist-info'
    b.mkdir()
    (b / 'METADATA').write_text(f'Metadata-Version: 2.1\nName: af-build-fixture-b\nVersion: {version}\n')
    # A real module in the disposable interpreter; no framework installation or network.
    (site / 'abstractcore.py').write_text('create_llm = object()\n' if imports_ok else 'raise ImportError("fixture import failure")\n')
    source = (ROOT / 'scripts/build.sh').read_text()
    start = source.index('    section "Python — Verification"')
    end = source.index('\n# ═', start)
    verification = source[start:end]  # includes the closing main Python-selection `fi`
    command = '''
section() { :; }
ok_line() { :; }
warn_line() { echo "$*"; }
af_pkg_indices() { echo 0; }
AF_PKG_ID=(abstractcore)
C_RED='' C_RESET=''
if true; then
''' + verification + '\nif $py_ok; then exit 0; else exit 1; fi\n'
    env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ.get('PATH', ''), PIP_DISABLE_PIP_VERSION_CHECK='1')
    result = subprocess.run(['bash', '-c', command], env=env, capture_output=True, text=True)
    assert result.returncode == expected, result.stdout + result.stderr
    if not compatible:
        assert 'af-build-fixture-b' in result.stdout.lower()
    if not imports_ok:
        assert 'Some imports failed' in result.stdout
