"""Local builds request install settings Runtime/Agent actually publish."""
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('package',['abstractruntime','abstractagent'])
@pytest.mark.parametrize('profile',['light','apple','gpu'])
def test_local_build_requests_declared_runtime_and_agent_extra(package, profile):
    source=(ROOT/'scripts/build.sh').read_text()
    match=re.search(r'^build_profile_extras\(\) \{\n.*?^\}',source,re.M|re.S)
    assert match, 'build_profile_extras is missing'
    command=match.group(0)+'\nbuild_profile_extras "$1" "$2"\n'
    value=subprocess.run(['bash','-c',command,'build-profile',package,profile],check=True,capture_output=True,text=True).stdout
    # Runtime and Agent expose light + apple/gpu (no all-apple/all-gpu aliases).
    # These are their public pyproject optional-dependency names.
    published_settings={'', '[apple]', '[gpu]'}
    assert value in published_settings, f'{package} does not publish {value}'
    assert value == ('' if profile == 'light' else f'[{profile}]')
