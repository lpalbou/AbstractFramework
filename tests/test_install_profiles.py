from __future__ import annotations

import json
import os
import re
import subprocess
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
        ROOT / "abstractcode" / "tui" / "Cargo.toml",
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
        ROOT / "abstractcode" / "tui" / "Cargo.toml",
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
    # AbstractCode ships as the crate `abstractcode` and the npm package
    # `@abstractframework/code`, not as a Python distribution, so the
    # meta-package must NOT pin it.
    assert not any(dep.startswith("abstractcode==") for dep in deps), (
        "abstractcode is no longer a PyPI distribution; drop the pin"
    )
    assert code_version, "expected a version in abstractcode/tui/Cargo.toml"
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

    release_versions = _release_versions()
    runtime_version = release_versions["abstractruntime"]
    gateway_version = release_versions["abstractgateway"]

    assert f"AbstractRuntime=={runtime_version}" in root_deps
    assert f"abstractgateway[apple]=={gateway_version}" in root_apple
    assert f"abstractgateway[gpu]=={gateway_version}" in root_gpu
    # The pinned Gateway must accept the pinned Runtime in every profile.
    assert f"AbstractRuntime>={runtime_version}" in gateway_deps
    assert f"AbstractRuntime[apple]>={runtime_version}" in gateway_apple
    assert f"AbstractRuntime[gpu]>={runtime_version}" in gateway_gpu
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
    assert {check["status"] for check in report["checks"]} <= {"ok", "warn", "error", "info"}


# --- bootstrap installers, manifest v2 and doctor (WS5) ---------------------------------------


def test_manifest_bootstrap_section_pins_the_released_gateway() -> None:
    from abstractframework.install_manifest import build_install_manifest

    manifest = build_install_manifest()
    bootstrap = manifest["bootstrap"]
    release_versions = _release_versions()

    assert manifest["schema_version"] == 2
    assert bootstrap["gateway_version"] == release_versions["abstractgateway"]
    assert bootstrap["python"] == "3.12"
    assert bootstrap["profile_extras"] == {"light": [], "apple": ["apple"], "gpu": ["gpu"]}
    assert bootstrap["scripts"]["unix"]["url"].endswith("/scripts/install.sh")
    assert bootstrap["scripts"]["windows"]["url"].endswith("/scripts/install.ps1")
    assert "| sh" in bootstrap["scripts"]["unix"]["one_liner"]
    assert "-ExecutionPolicy ByPass" in bootstrap["scripts"]["windows"]["one_liner"]
    for flag in bootstrap["flags"]:
        assert flag["sh"].startswith("--") and flag["ps"].startswith("-")


def test_manifest_post_install_is_console_first() -> None:
    from abstractframework.install_manifest import build_install_manifest

    post = build_install_manifest()["post_install"]
    assert post["entrypoint"] == "console"
    assert post["gateway"][:2] == ["abstractgateway", "serve"]
    assert "127.0.0.1" in post["gateway"]
    assert post["console_url"].endswith("/console")
    assert post["claim"] == ["abstractgateway-config", "claim-url"]
    assert post["claim_fallback"]["token_file"].endswith("auth/bootstrap-admin-token")
    # The old config front door must not come back: the console configures providers.
    assert "core_config" not in post
    assert all(cmd[:2] == ["npx", "-y"] for cmd in post["apps"])


def test_manifest_validates_against_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (ROOT / "docs" / "installers" / "install-manifest.schema.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (ROOT / "docs" / "installers" / "install-manifest.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(manifest, schema)
    broken = dict(manifest)
    broken.pop("bootstrap")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(broken, schema)


def _script_pins(text: str) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 3:
            pins[f"{parts[0]}:{parts[1]}"] = parts[2]
    return pins


def test_bootstrap_scripts_embed_the_manifest_pins() -> None:
    import subprocess

    from abstractframework import NPM_RELEASE_VERSIONS
    from abstractframework.install_manifest import build_install_manifest

    manifest = build_install_manifest()
    out = subprocess.run(
        ["sh", str(ROOT / "scripts" / "install.sh"), "--print-versions"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    sh_pins = _script_pins(out)
    assert sh_pins["pypi:abstractgateway"] == manifest["bootstrap"]["gateway_version"]
    for package, version in NPM_RELEASE_VERSIONS.items():
        assert sh_pins[f"npm:{package}"] == version

    ps1 = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    match = re.search(r"^\$AfGatewayPinDefault = '([^']+)'", ps1, flags=re.MULTILINE)
    assert match and match.group(1) == manifest["bootstrap"]["gateway_version"]
    ps_apps = re.search(r"^\$AfNpmApps = @\((.*)\)$", ps1, flags=re.MULTILINE)
    assert ps_apps is not None
    for package, version in NPM_RELEASE_VERSIONS.items():
        assert f"'{package}@{version}'" in ps_apps.group(1)
    sh_crates = {k: v for k, v in sh_pins.items() if k.startswith("crates:")}
    for key, version in sh_crates.items():
        assert f"'{key.split(':', 1)[1]}@{version}'" in ps1


def test_bootstrap_script_crates_match_crate_release_versions() -> None:
    import subprocess

    from abstractframework import CRATE_RELEASE_VERSIONS

    out = subprocess.run(
        ["sh", str(ROOT / "scripts" / "install.sh"), "--print-versions"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    sh_crates = {
        key.split(":", 1)[1]: version
        for key, version in _script_pins(out).items()
        if key.startswith("crates:")
    }
    # --with-console and --with-code-cli install exactly these two crates.
    assert set(sh_crates) == {"abstractgateway-console", "abstractcode"}
    for crate, version in sh_crates.items():
        assert CRATE_RELEASE_VERSIONS[crate] == version


def test_install_sh_reads_the_pin_from_the_manifest(tmp_path: Path) -> None:
    import subprocess

    manifest = tmp_path / "install-manifest.json"
    manifest.write_text('{\n  "bootstrap": {\n    "gateway_version": "9.9.9"\n  }\n}\n')
    out = subprocess.run(
        [
            "sh", str(ROOT / "scripts" / "install.sh"), "--print", "--profile", "light",
            "--port", "18999", "--manifest", str(manifest), "--no-tray",
        ],
        check=True,
        capture_output=True,
        text=True,
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "TERM": "dumb"},
    ).stdout
    assert "abstractgateway==9.9.9" in out
    assert "nothing was changed" in out
    assert not (tmp_path / ".local").exists(), "--print must not install anything"


# --- prebuilt wheels only: no C compiler / Xcode tools needed --------------------------------

_COMPILED_EXTRAS = ["stable-diffusion-cpp-python", "aec-audio-processing"]
_ALWAYS = ["webrtcvad; sys_platform == 'never'", "vllm>=0.6.0,<1.0.0; sys_platform == 'linux'"]
_DEFAULT_OVERRIDES = _ALWAYS + [f"{p}; sys_platform == 'never'" for p in _COMPILED_EXTRAS]
_NO_GGUF_OVERRIDES = _DEFAULT_OVERRIDES + ["llama-cpp-python; sys_platform == 'never'"]
_NO_BUILD = ["webrtcvad", "vllm", *_COMPILED_EXTRAS, "llama-cpp-python"]
_SKIPPED = "Skipped compiled extras (stable-diffusion.cpp, echo cancellation): re-run with {flag} after installing a C compiler."
_GGUF_SKIPPED = "GGUF (llama.cpp) skipped: no prebuilt wheel for this machine; re-run with {flag} after installing a C compiler"
_LLAMA = "https://abetlen.github.io/llama-cpp-python/whl"


def _fake_bin(tmp_path: Path, *, compiler: bool, machine: str | None = None) -> Path:
    """xcode-select/cc stubs (`compiler=False` simulates a Mac without Xcode CLT) and an
    optional `uname -m` override to simulate another CPU."""
    fake = tmp_path / "fakebin"
    fake.mkdir()
    for name in ("xcode-select", "cc"):
        if name == "cc" and not compiler:
            continue
        stub = fake / name
        stub.write_text(f"#!/bin/sh\nexit {0 if compiler else 2}\n")
        stub.chmod(0o755)
    if machine:
        uname = fake / "uname"
        real = __import__("shutil").which("uname")
        uname.write_text(f'#!/bin/sh\ncase "$1" in -m) echo {machine} ;; *) {real} "$@" ;; esac\n')
        uname.chmod(0o755)
    return fake


def _host() -> tuple[str, str, str]:
    """(profile with local engines, expected llama.cpp pin, wheel kind) for this machine."""
    import platform
    import sys

    machine = platform.machine()
    if sys.platform == "darwin" and machine == "arm64":
        return "apple", "0.3.28", "metal"
    if sys.platform.startswith("linux") and machine in ("x86_64", "aarch64"):
        return "gpu", "0.3.35", "cpu"
    pytest.skip("install.sh wheel selection is tested on Apple Silicon and glibc Linux")


def _install_sh_print(tmp_path: Path, *extra: str, profile: str | None = None, compiler: bool = True,
                      machine: str | None = None) -> subprocess.CompletedProcess[str]:
    fake = _fake_bin(tmp_path, compiler=compiler, machine=machine)
    return subprocess.run(
        ["sh", str(ROOT / "scripts" / "install.sh"), "--print", "--profile", profile or _host()[0], "--port", "18999", *extra],
        capture_output=True,
        text=True,
        env={"HOME": str(tmp_path), "PATH": f"{fake}:/usr/bin:/bin:/usr/sbin:/sbin", "TERM": "dumb"},
    )


def _printed_block(out: str, marker: str) -> list[str]:
    lines = out.splitlines()
    head = next(i for i, line in enumerate(lines) if marker in line)
    block = []
    for line in lines[head + 1:]:
        if not line.startswith("      "):
            break
        block.append(line.strip())
    return block


def _printed_overrides(out: str) -> list[str]:
    return _printed_block(out, "uv-overrides.txt (written at install time")


def _install_line(out: str) -> str:
    return next(line for line in out.splitlines() if " tool install --python 3.12 " in line)


@pytest.mark.parametrize("profile", ["light", "local"])
def test_install_sh_default_takes_llama_cpp_from_the_prebuilt_wheel(tmp_path: Path, profile: str) -> None:
    local, pin, kind = _host()
    proc = _install_sh_print(tmp_path, profile=local if profile == "local" else "light", compiler=False)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert _printed_overrides(out) == _DEFAULT_OVERRIDES
    assert _printed_block(out, "uv-constraints.txt:") == [f"llama-cpp-python=={pin}"]
    install = _install_line(out)
    # uv splits --overrides/--constraints values at whitespace (macOS "Application
    # Support"), so the install runs from the data dir with relative file names
    assert install.lstrip().startswith("$ cd ")
    assert (
        f"--with 'webrtcvad-wheels>=2.0.14' --with llama-cpp-python=={pin} --constraints uv-constraints.txt "
        f"--find-links {_LLAMA}/{kind}/llama-cpp-python/ --overrides uv-overrides.txt "
    ) in install
    assert " ".join(f"--no-build-package {p}" for p in _NO_BUILD) in install
    assert re.search(r" 'abstractgateway\[[a-z,]+\]==\S+'$", install.rstrip()), install
    assert f"GGUF:       llama-cpp-python {pin} ({kind} wheel from {_LLAMA}/{kind}/llama-cpp-python/)" in out
    assert "it is retried without it" in out
    assert (_SKIPPED.format(flag="--full") in out) == (profile == "local")
    assert not (tmp_path / "Library").exists() and not (tmp_path / ".local").exists()


def test_install_sh_skips_gguf_where_no_wheel_exists(tmp_path: Path) -> None:
    _host()
    proc = _install_sh_print(tmp_path, profile="light", compiler=False, machine="riscv64")
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert _GGUF_SKIPPED.format(flag="--full") in out
    assert _printed_overrides(out) == _NO_GGUF_OVERRIDES
    install = _install_line(out)
    assert "--find-links" not in install and "--constraints" not in install
    assert "--with 'webrtcvad-wheels>=2.0.14' --overrides uv-overrides.txt " in install
    assert "GGUF:       skipped (no prebuilt wheel for " in out


def test_install_sh_retries_without_llama_cpp_when_the_wheel_fails(tmp_path: Path) -> None:
    """A real (non --print) run against a fake uv whose install fails when it is given the
    llama.cpp wheel source: the script must warn, retry without llama-cpp-python, succeed."""
    _host()
    fake = _fake_bin(tmp_path, compiler=False)
    tool_bin = tmp_path / "toolbin"
    calls = tmp_path / "uv-calls.log"
    uv = fake / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        f'echo "$*" >> "{calls}"\n'
        'case "$1 $2" in\n'
        '  "--version "*) echo "uv 0.0.0" ;;\n'
        f'  "tool dir") echo "{tool_bin}" ;;\n'
        '  "tool install")\n'
        '    for a in "$@"; do [ "$a" = --find-links ] && { echo "simulated: no wheel" >&2; exit 2; }; done\n'
        f'    mkdir -p "{tool_bin}" && printf "#!/bin/sh\\nexit 1\\n" > "{tool_bin}/abstractgateway" && chmod +x "{tool_bin}/abstractgateway" ;;\n'
        "esac\n"
        "exit 0\n"
    )
    uv.chmod(0o755)
    proc = subprocess.run(
        ["sh", str(ROOT / "scripts" / "install.sh"), "--profile", "light", "--port", "18998",
         "--no-start", "--no-service", "--no-open", "--no-modify-path"],
        capture_output=True, text=True,
        env={"HOME": str(tmp_path), "PATH": f"{fake}:/usr/bin:/bin:/usr/sbin:/sbin", "TERM": "dumb",
             "XDG_DATA_HOME": str(tmp_path / "data")},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    installs = [line for line in calls.read_text().splitlines() if line.startswith("tool install ")]
    assert len(installs) == 2 and "--find-links" in installs[0] and "--find-links" not in installs[1]
    assert _GGUF_SKIPPED.format(flag="--full") in proc.stdout
    assert "GGUF:       skipped (the prebuilt " in proc.stdout
    overrides = next((tmp_path / "data").rglob("uv-overrides.txt")) if (tmp_path / "data").exists() else next(tmp_path.rglob("uv-overrides.txt"))
    assert overrides.read_text().splitlines() == _NO_GGUF_OVERRIDES


def test_install_sh_full_builds_the_compiled_extras(tmp_path: Path) -> None:
    proc = _install_sh_print(tmp_path, "--full", compiler=True)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert _printed_overrides(out) == _ALWAYS
    install = _install_line(out)
    assert "--with llama-cpp-python --overrides uv-overrides.txt --no-build-package webrtcvad --no-build-package vllm 'abstractgateway[" in install
    assert "--find-links" not in install
    for pkg in _COMPILED_EXTRAS:
        assert pkg not in install
    assert "Skipped compiled extras" not in out
    assert "GGUF:       llama-cpp-python built from source (--full)" in out


def test_install_sh_full_stops_without_a_compiler(tmp_path: Path) -> None:
    import sys

    if sys.platform != "darwin":
        pytest.skip("simulating a missing compiler needs the macOS xcode-select probe")
    proc = _install_sh_print(tmp_path, "--full", compiler=False)
    assert proc.returncode != 0
    assert "xcode-select --install" in proc.stderr
    assert " tool install " not in proc.stdout


def test_install_ps1_carries_the_same_lists_as_install_sh() -> None:
    sh = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    ps1 = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    sh_extras = re.search(r'^AF_COMPILED_EXTRAS="([^"]+)"$', sh, flags=re.M)
    ps_extras = re.search(r"^\$AfCompiledExtras = @\((.*)\)$", ps1, flags=re.M)
    assert sh_extras and ps_extras
    assert sh_extras.group(1).split() == re.findall(r"'([^']+)'", ps_extras.group(1)) == _COMPILED_EXTRAS
    assert 'AF_WITH_WHEELS="webrtcvad-wheels>=2.0.14"' in sh
    assert "$AfWithWheels = 'webrtcvad-wheels>=2.0.14'" in ps1
    for line in _ALWAYS:
        assert f'echo "{line}"' in sh
        assert f'"{line}"' in ps1
    assert f"AF_SKIPPED_LINE=\"{_SKIPPED.format(flag='--full')}\"" in sh
    assert f"$AfSkippedLine = '{_SKIPPED.format(flag='-Full')}'" in ps1
    assert f"$AfGgufSkipped = '{_GGUF_SKIPPED.format(flag='-Full')}'" in ps1
    assert f'AF_LLAMA_INDEX="{_LLAMA}"' in sh and f"$AfLlamaIndex = '{_LLAMA}'" in ps1
    sh_cpu = re.search(r'^AF_LLAMA_CPU_PIN="([^"]+)"$', sh, flags=re.M)
    ps_cpu = re.search(r"^\$AfLlamaCpuPin = '([^']+)'$", ps1, flags=re.M)
    assert sh_cpu and ps_cpu and sh_cpu.group(1) == ps_cpu.group(1)
    # relative names + Push-Location: uv splits --overrides/--constraints values at whitespace
    assert "'--constraints', 'uv-constraints.txt'" in ps1 and "@('--overrides', 'uv-overrides.txt')" in ps1
    assert "Push-Location -LiteralPath $DataDir" in ps1
    assert "if (Install-Gateway $true -Soft) {" in ps1 and "Write-Warn2 $AfGgufSkipped" in ps1


@pytest.mark.skipif(__import__("shutil").which("pwsh") is None, reason="needs PowerShell 7 (pwsh)")
def test_install_ps1_parses_and_prints_the_prebuilt_wheel_install_command(tmp_path: Path) -> None:
    script = ROOT / "scripts" / "install.ps1"
    parse = subprocess.run(
        [
            "pwsh", "-NoProfile", "-Command",
            "$e=$null; $t=$null; [System.Management.Automation.Language.Parser]::ParseFile("
            f"'{script}', [ref]$t, [ref]$e) | Out-Null; $e.Count",
        ],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert parse == "0"
    env = {**os.environ, "HOME": str(tmp_path), "USERPROFILE": str(tmp_path), "LOCALAPPDATA": str(tmp_path / "lad"),
           "PROCESSOR_ARCHITECTURE": "AMD64"}
    argv = ["pwsh", "-NoProfile", "-File", str(script), "-Print", "-Profile", "gpu", "-Port", "18999"]
    out = subprocess.run(argv, check=True, capture_output=True, text=True, env=env).stdout
    assert _printed_overrides(out) == _DEFAULT_OVERRIDES
    assert _printed_block(out, "uv-constraints.txt:") == ["llama-cpp-python==0.3.35"]
    install = _install_line(out)
    assert (
        "--with 'webrtcvad-wheels>=2.0.14' --with llama-cpp-python==0.3.35 --constraints uv-constraints.txt "
        f"--find-links {_LLAMA}/cpu/llama-cpp-python/ --overrides uv-overrides.txt "
    ) in install
    assert " ".join(f"--no-build-package {p}" for p in _NO_BUILD) in install
    assert _SKIPPED.format(flag="-Full") in out
    assert f"GGUF:       llama-cpp-python 0.3.35 (cpu wheel from {_LLAMA}/cpu/llama-cpp-python/)" in out
    assert not (tmp_path / "lad").exists(), "-Print must not write anything"
    if __import__("shutil").which("cl.exe") is None:
        full = subprocess.run(argv + ["-Full"], capture_output=True, text=True, env=env)
        assert full.returncode != 0 and " tool install " not in full.stdout


def _serve(routes: dict[str, object]):
    import http.server
    import threading

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            body = routes.get(self.path)
            if body is None:
                self.send_response(404)
                self.end_headers()
                return
            data = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self) -> None:  # noqa: N802 - the doctor must never mutate
            raise AssertionError("doctor sent a POST")

        def log_message(self, *args: object) -> None:
            return

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_doctor_probes_gateway_and_engines_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from abstractframework.cli import build_doctor_report, main

    server = _serve(
        {
            "/api/health": {"status": "healthy", "service": "abstractgateway"},
            "/api/version": {"version": "0.34.3"},
            "/v1/models": {"data": [{"id": "qwen3-8b"}, {"id": "gemma"}]},
        }
    )
    base = f"http://127.0.0.1:{server.server_address[1]}"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    cfg = fake_bin / "abstractgateway-config"
    cfg.write_text(
        "#!/bin/sh\n"
        'echo \'{"gateway": {"data_dir": "/data/gw", "auth_configured": true, '
        '"store_backend": "file"}, "service": {"installed": true}}\'\n'
    )
    cfg.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("ABSTRACTGATEWAY_URL", base)
    monkeypatch.setenv("OLLAMA_BASE_URL", base)
    monkeypatch.setenv("LMSTUDIO_BASE_URL", f"{base}/v1")
    try:
        report = build_doctor_report(include_environment=True, include_network=True, timeout=2)
    finally:
        server.shutdown()

    checks = {check["id"]: check for check in report["checks"]}  # type: ignore[index]
    assert report["schema"] == "abstractframework_doctor_v2"
    assert {"os", "arch", "python"} <= set(report["platform"])  # type: ignore[arg-type]
    assert checks["gateway"]["status"] == "ok"
    assert checks["gateway"]["data"]["url"] == base
    assert checks["gateway:config"]["data"]["data_dir"] == "/data/gw"
    assert checks["gateway:config"]["data"]["service"] == {"installed": True}
    assert checks["engine:ollama"]["status"] == "ok"
    assert checks["engine:ollama"]["data"]["version"] == "0.34.3"
    assert checks["engine:lmstudio"]["data"]["models"] == 2
    for key in ("python", "uv", "node", "disk", "profile:apple", "profile:gpu"):
        assert key in checks
    assert {check["status"] for check in report["checks"]} <= {"ok", "warn", "error", "info"}  # type: ignore[union-attr]

    assert main(["doctor", "--json", "--no-network"]) in (0, 1)


def test_doctor_reports_unreachable_gateway_as_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    from abstractframework.cli import build_doctor_report

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()  # nothing listens here now
    monkeypatch.setenv("ABSTRACTGATEWAY_URL", f"http://127.0.0.1:{port}")
    monkeypatch.setenv("OLLAMA_BASE_URL", f"http://127.0.0.1:{port}")
    monkeypatch.setenv("LMSTUDIO_BASE_URL", f"http://127.0.0.1:{port}")
    monkeypatch.setenv("PATH", "/nonexistent")
    report = build_doctor_report(include_environment=False, include_network=True, timeout=1)
    checks = {check["id"]: check for check in report["checks"]}  # type: ignore[index]
    assert checks["gateway"]["status"] == "warn"
    assert checks["engine:ollama"]["status"] == "info"
    assert checks["engine:lmstudio"]["status"] == "info"
    assert checks["gateway:config"]["status"] == "info"
