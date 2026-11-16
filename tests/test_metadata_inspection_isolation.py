"""Inspecting the profile must never initialize a component or its user configuration."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run_isolated(script, tmp_path):
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path))
    result = subprocess.run([sys.executable, '-I', '-c', script, str(ROOT)],
        env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


GUARD = '''
import ast, importlib.abc, pathlib, sys
root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root))
tree = ast.parse((root / 'abstractframework/__init__.py').read_text())
blocked = set()
for node in tree.body:
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == 'PACKAGE_DISTRIBUTIONS':
        blocked.update(ast.literal_eval(node.value))
assert 'abstractcore' in blocked, 'component import guard must include Core'
class ComponentImportAttempt(BaseException): pass
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in blocked:
            raise ComponentImportAttempt('metadata inspection imported ' + fullname)
sys.meta_path.insert(0, Guard())
import socket
def refuse_network(*args, **kwargs):
    raise ComponentImportAttempt('metadata inspection attempted network access')
socket.socket.connect = refuse_network
'''


def test_profile_version_listing_doctor_and_manifest_never_import_components(tmp_path):
    run_isolated(GUARD + '''
import contextlib, io, json
import abstractframework as framework
assert framework.get_release_profile()['packages']
assert all(isinstance(v, str) for v in framework.get_installed_packages().values())
with contextlib.redirect_stdout(io.StringIO()): framework.print_status()
from abstractframework.cli import main
out = io.StringIO()
with contextlib.redirect_stdout(out): result = main(['doctor', '--no-environment', '--json'])
assert result in (0, 1)
assert json.loads(out.getvalue())['schema'] == 'abstractframework_doctor_v2'
with contextlib.redirect_stdout(io.StringIO()): assert main(['manifest']) == 0
''', tmp_path)


def test_convenience_exports_resolve_lazily_with_original_identity(tmp_path):
    run_isolated(GUARD + '''
import types
import abstractframework as framework
assert 'abstractcore' not in sys.modules
assert {'create_llm', 'GenerateResponse'} <= set(dir(framework))
core = types.ModuleType('abstractcore')
def factory(*args, **kwargs): return args, kwargs
class Response: pass
core.create_llm = factory
core.GenerateResponse = Response
sys.modules['abstractcore'] = core
from abstractframework import create_llm, GenerateResponse
assert create_llm is factory and GenerateResponse is Response
assert framework.create_llm is factory
assert {'create_llm', 'GenerateResponse'} <= set(framework.__all__)
try: framework.nonexistent_export
except AttributeError: pass
else: raise AssertionError('unknown export accepted')
''', tmp_path)
