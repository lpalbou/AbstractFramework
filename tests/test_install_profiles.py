from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Iterable

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _version_from_regex(path: Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    assert match is not None
    return match.group(1)


def _dependency_version(dependencies: Iterable[str], name: str) -> str:
    normalized = name.lower()
    for dep in dependencies:
        base = dep.split(";", 1)[0].strip()
        if "==" not in base:
            continue
        dep_name, version = base.split("==", 1)
        dep_name = dep_name.split("[", 1)[0].lower()
        if dep_name == normalized:
            return version.strip()
    raise AssertionError(f"Missing pinned dependency for {name}")


def _release_versions() -> dict[str, str]:
    namespace: dict[str, object] = {}
    source = ROOT / "abstractframework" / "__init__.py"
    exec(source.read_text(encoding="utf-8"), namespace)
    return dict(namespace["RELEASE_VERSIONS"])  # type: ignore[index]


def test_framework_profiles_expose_only_base_apple_gpu() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    opt = pyproject["project"]["optional-dependencies"]

    assert set(opt.keys()) == {"apple", "gpu"}


def test_framework_profile_pins_match_release_versions() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps: list[str] = pyproject["project"]["dependencies"]
    opt = pyproject["project"]["optional-dependencies"]
    release_versions = _release_versions()

    assert _dependency_version(deps, "abstractcore") == release_versions["abstractcore"]
    assert _dependency_version(deps, "AbstractRuntime") == release_versions["abstractruntime"]
    assert _dependency_version(deps, "abstractagent") == release_versions["abstractagent"]
    assert _dependency_version(deps, "abstractgateway") == release_versions["abstractgateway"]
    assert _dependency_version(deps, "abstractflow") == release_versions["abstractflow"]
    assert _dependency_version(deps, "abstractcode") == release_versions["abstractcode"]
    assert _dependency_version(deps, "abstractassistant") == release_versions["abstractassistant"]
    assert _dependency_version(deps, "AbstractMemory") == release_versions["abstractmemory"]
    assert _dependency_version(deps, "abstractsemantics") == release_versions["abstractsemantics"]
    assert _dependency_version(deps, "abstractvoice") == release_versions["abstractvoice"]
    assert _dependency_version(deps, "abstractvision") == release_versions["abstractvision"]
    assert _dependency_version(deps, "abstractmusic") == release_versions["abstractmusic"]

    assert f"abstractgateway[apple]=={release_versions['abstractgateway']}" in opt["apple"]
    assert f"abstractflow[apple]=={release_versions['abstractflow']}" in opt["apple"]
    assert any(
        dep.startswith(f"abstractassistant[apple]=={release_versions['abstractassistant']}")
        for dep in opt["apple"]
    )

    assert f"abstractgateway[gpu]=={release_versions['abstractgateway']}" in opt["gpu"]
    assert f"abstractflow[gpu]=={release_versions['abstractflow']}" in opt["gpu"]
    assert f"abstractassistant[gpu]=={release_versions['abstractassistant']}" in opt["gpu"]


def test_framework_profile_pins_match_sibling_repo_versions_when_available() -> None:
    required_paths = [
        ROOT / "abstractcore" / "abstractcore" / "utils" / "version.py",
        ROOT / "abstractruntime" / "pyproject.toml",
        ROOT / "abstractagent" / "pyproject.toml",
        ROOT / "abstractgateway" / "pyproject.toml",
        ROOT / "abstractflow" / "abstractflow" / "_version.py",
        ROOT / "abstractcode" / "pyproject.toml",
        ROOT / "abstractassistant" / "pyproject.toml",
    ]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        pytest.skip("Sibling package checkouts are not present in this standalone checkout.")

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
    release_versions = _release_versions()

    assert components["framework_full"]["extras"] == ["apple"]
    assert components["framework_full"]["version"] == tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]

    assert components["abstractcore"]["extras"] == ["all-apple"]
    assert components["abstractruntime"]["extras"] == ["apple"]
    assert components["abstractgateway"]["extras"] == ["apple"]
    assert components["abstractagent"]["extras"] == ["apple"]

    assert components["abstractcore"]["version"] == release_versions["abstractcore"]
    assert components["abstractruntime"]["version"] == release_versions["abstractruntime"]
    assert components["abstractgateway"]["version"] == release_versions["abstractgateway"]
    assert components["abstractagent"]["version"] == release_versions["abstractagent"]
    assert components["abstractflow"]["version"] == release_versions["abstractflow"]
    assert components["abstractcode"]["version"] == release_versions["abstractcode"]
    assert components["abstractassistant"]["version"] == release_versions["abstractassistant"]
    assert components["abstractmemory"]["version"] == release_versions["abstractmemory"]
    assert components["abstractsemantics"]["version"] == release_versions["abstractsemantics"]
    assert components["abstractvoice"]["version"] == release_versions["abstractvoice"]
    assert components["abstractvision"]["version"] == release_versions["abstractvision"]
    assert components["abstractmusic"]["version"] == release_versions["abstractmusic"]
