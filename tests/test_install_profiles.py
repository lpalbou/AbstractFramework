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


def test_framework_profiles_expose_only_apple_gpu_extras() -> None:
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
    assert _dependency_version(deps, "abstractcode") == release_versions["abstractcode"]
    assert _dependency_version(deps, "abstractassistant") == release_versions["abstractassistant"]
    assert _dependency_version(deps, "AbstractMemory") == release_versions["abstractmemory"]
    assert _dependency_version(deps, "abstractsemantics") == release_versions["abstractsemantics"]
    assert _dependency_version(deps, "abstractvoice") == release_versions["abstractvoice"]
    assert _dependency_version(deps, "abstractvision") == release_versions["abstractvision"]
    assert _dependency_version(deps, "abstractmusic") == release_versions["abstractmusic"]

    assert f"abstractgateway[apple]=={release_versions['abstractgateway']}" in opt["apple"]
    assert any(
        dep.startswith(f"abstractassistant[apple]=={release_versions['abstractassistant']}")
        for dep in opt["apple"]
    )

    assert f"abstractgateway[gpu]=={release_versions['abstractgateway']}" in opt["gpu"]
    assert f"abstractassistant[gpu]=={release_versions['abstractassistant']}" in opt["gpu"]


def test_framework_profile_pins_match_sibling_repo_versions_when_available() -> None:
    required_paths = [
        ROOT / "abstractcore" / "abstractcore" / "utils" / "version.py",
        ROOT / "abstractruntime" / "pyproject.toml",
        ROOT / "abstractagent" / "pyproject.toml",
        ROOT / "abstractgateway" / "pyproject.toml",
        ROOT / "abstractflow" / "package.json",
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
    flow_version = json.loads((ROOT / "abstractflow" / "package.json").read_text(encoding="utf-8"))[
        "version"
    ]
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
    assert f"abstractcode=={code_version}" in deps
    assert f"abstractassistant=={assistant_version}" in deps

    assert f"abstractgateway[apple]=={gateway_version}" in opt["apple"]
    assert any(
        dep.startswith(f"abstractassistant[apple]=={assistant_version}")
        for dep in opt["apple"]
    )

    assert f"abstractgateway[gpu]=={gateway_version}" in opt["gpu"]
    assert f"abstractassistant[gpu]=={assistant_version}" in opt["gpu"]
    from abstractframework import NPM_RELEASE_VERSIONS

    assert NPM_RELEASE_VERSIONS["@abstractframework/flow"] == flow_version


def test_framework_profiles_inherit_runtime_pdf_stack() -> None:
    runtime_pyproject = ROOT / "abstractruntime" / "pyproject.toml"
    gateway_pyproject = ROOT / "abstractgateway" / "pyproject.toml"
    if not runtime_pyproject.exists() or not gateway_pyproject.exists():
        pytest.skip("Sibling Runtime/Gateway checkouts are not present in this standalone checkout.")

    root_project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    gateway_project = tomllib.loads(gateway_pyproject.read_text(encoding="utf-8"))["project"]
    runtime_project = tomllib.loads(runtime_pyproject.read_text(encoding="utf-8"))["project"]

    root_deps = "\n".join(root_project["dependencies"])
    root_apple = "\n".join(root_project["optional-dependencies"]["apple"])
    root_gpu = "\n".join(root_project["optional-dependencies"]["gpu"])
    gateway_deps = "\n".join(gateway_project["dependencies"])
    gateway_apple = "\n".join(gateway_project["optional-dependencies"]["apple"])
    gateway_gpu = "\n".join(gateway_project["optional-dependencies"]["gpu"])
    runtime_deps = "\n".join(runtime_project["dependencies"])

    assert "AbstractRuntime==0.4.29" in root_deps
    assert "abstractgateway[apple]==0.2.28" in root_apple
    assert "abstractgateway[gpu]==0.2.28" in root_gpu
    assert "AbstractRuntime>=0.4.29" in gateway_deps
    assert "AbstractRuntime[apple]>=0.4.29" in gateway_apple
    assert "AbstractRuntime[gpu]>=0.4.29" in gateway_gpu
    assert "pypdf<7.0.0,>=6.0.0" in runtime_deps
    assert "reportlab<5.0.0,>=4.0.0" in runtime_deps


def test_generated_install_manifest_matches_checked_in_manifest() -> None:
    from abstractframework.install_manifest import build_install_manifest, manifest_json

    manifest_path = ROOT / "docs" / "installers" / "install-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest == build_install_manifest()
    assert manifest_path.read_text(encoding="utf-8") == manifest_json()


def test_install_manifest_profiles_are_generated_from_root_pins() -> None:
    from abstractframework import NPM_RELEASE_VERSIONS
    from abstractframework.install_manifest import build_install_manifest

    manifest = build_install_manifest()
    profiles = {item["id"]: item for item in manifest["profiles"]}
    packages = {item["id"]: item for item in manifest["python_packages"]}
    npm_apps = {item["package"]: item for item in manifest["npm_apps"]}
    release_versions = _release_versions()
    framework_version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["version"]

    assert set(profiles) == {"light", "apple", "gpu"}
    assert profiles["light"]["pip_requirements"] == [f"abstractframework=={framework_version}"]
    assert profiles["apple"]["pip_requirements"] == [
        f"abstractframework[apple]=={framework_version}"
    ]
    assert profiles["gpu"]["pip_requirements"] == [f"abstractframework[gpu]=={framework_version}"]
    assert profiles["light"]["local_inference"] is False
    assert profiles["apple"]["local_inference"] is True
    assert profiles["gpu"]["local_inference"] is True

    for package_id, version in release_versions.items():
        assert packages[package_id]["version"] == version

    for package_name, version in NPM_RELEASE_VERSIONS.items():
        assert npm_apps[package_name]["version"] == version


def test_cli_manifest_check_and_doctor_report() -> None:
    from abstractframework.cli import build_doctor_report, main

    assert (
        main(["manifest", "--check", str(ROOT / "docs" / "installers" / "install-manifest.json")])
        == 0
    )

    report = build_doctor_report(include_environment=False)
    assert report["abstractframework"] == tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]
    assert {check["status"] for check in report["checks"]} <= {"ok", "warn", "error"}
