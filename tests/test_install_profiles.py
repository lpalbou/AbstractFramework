from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _version_from_regex(path: Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    assert match is not None
    return match.group(1)


def test_framework_profiles_expose_only_base_apple_gpu() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    opt = pyproject["project"]["optional-dependencies"]

    assert set(opt.keys()) == {"apple", "gpu"}


def test_framework_profile_pins_match_repo_versions() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps: list[str] = pyproject["project"]["dependencies"]
    opt = pyproject["project"]["optional-dependencies"]

    core_version = _version_from_regex(
        ROOT / "abstractcore" / "abstractcore" / "utils" / "version.py",
        r'__version__\s*=\s*"([^"]+)"',
    )
    runtime_version = _version_from_regex(
        ROOT / "abstractruntime" / "pyproject.toml",
        r'^\s*version\s*=\s*"([^"]+)"\s*$',
    )
    agent_version = _version_from_regex(
        ROOT / "abstractagent" / "pyproject.toml",
        r'^\s*version\s*=\s*"([^"]+)"\s*$',
    )
    gateway_version = _version_from_regex(
        ROOT / "abstractgateway" / "pyproject.toml",
        r'^\s*version\s*=\s*"([^"]+)"\s*$',
    )
    flow_version = _version_from_regex(
        ROOT / "abstractflow" / "abstractflow" / "_version.py",
        r'__version__\s*=\s*"([^"]+)"',
    )
    code_version = _version_from_regex(
        ROOT / "abstractcode" / "pyproject.toml",
        r'^\s*version\s*=\s*"([^"]+)"\s*$',
    )
    assistant_version = _version_from_regex(
        ROOT / "abstractassistant" / "pyproject.toml",
        r'^\s*version\s*=\s*"([^"]+)"\s*$',
    )

    assert f"abstractcore=={core_version}" in deps
    assert f"AbstractRuntime=={runtime_version}" in deps
    assert f"abstractagent=={agent_version}" in deps
    assert f"abstractgateway=={gateway_version}" in deps
    assert f"abstractflow=={flow_version}" in deps
    assert f"abstractcode=={code_version}" in deps
    assert f"abstractassistant=={assistant_version}" in deps

    assert f"abstractgateway[apple]=={gateway_version}" in opt["apple"]
    assert f"abstractflow[apple]=={flow_version}" in opt["apple"]
    assert any(
        dep.startswith(f"abstractassistant[apple]=={assistant_version}")
        for dep in opt["apple"]
    )

    assert f"abstractgateway[gpu]=={gateway_version}" in opt["gpu"]
    assert f"abstractflow[gpu]=={flow_version}" in opt["gpu"]
    assert f"abstractassistant[gpu]=={assistant_version}" in opt["gpu"]


def test_macos_installer_framework_full_uses_framework_apple_profile() -> None:
    manifest = json.loads((ROOT / "abstractinstallers" / "abstractframework-macos" / "manifest.local.json").read_text())
    components = {item["id"]: item for item in manifest["components"]}

    assert components["framework_full"]["extras"] == ["apple"]
