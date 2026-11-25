"""
AbstractFramework unified distribution package.

This package provides:
- a single install entrypoint for the full AbstractFramework ecosystem
- lightweight helpers to inspect installed component versions

Most implementation functionality still lives in component projects.
"""

from __future__ import annotations

from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from abstractcore import GenerateResponse as GenerateResponse, create_llm as create_llm

__version__ = "0.14.5"
__author__ = "Laurent-Philippe Albou"
__license__ = "MIT"

RELEASE_VERSIONS: dict[str, str] = {
    "abstractcore": "2.39.0",
    "abstractruntime": "0.21.0",
    "abstractagent": "0.6.1",
    "abstractgateway": "0.24.1",
    "abstractskill": "0.3.13",
    "abstractmemory": "0.5.2",
    "abstractsemantics": "0.0.5",
    "abstractvoice": "0.21.1",
    "abstractvision": "0.3.36",
    "abstractmusic": "0.1.17",
    "abstract3d": "0.3.2",
    "abstractassistant": "0.19.1",
    "abstractcamera": "0.2.1",
    "abstractavatar": "0.2.0",
    "abstractnote": "0.3.1"
}

PACKAGE_DISTRIBUTIONS: dict[str, str] = {
    "abstractcore": "abstractcore",
    "abstractruntime": "AbstractRuntime",
    "abstractagent": "abstractagent",
    "abstractgateway": "abstractgateway",
    "abstractskill": "abstractskill",
    "abstractmemory": "AbstractMemory",
    "abstractsemantics": "abstractsemantics",
    "abstractvoice": "abstractvoice",
    "abstractvision": "abstractvision",
    "abstractmusic": "abstractmusic",
    "abstract3d": "abstract3d",
    "abstractassistant": "abstractassistant",
    "abstractcamera": "abstractcamera",
    "abstractavatar": "abstractavatar",
    "abstractnote": "abstractnote",
}

NPM_RELEASE_VERSIONS: dict[str, str] = {
    "@abstractframework/flow": "0.14.2",
    "@abstractframework/code": "0.16.4",
    "@abstractframework/observer": "0.13.1",
    "@abstractframework/continuum": "0.8.1",
    "@abstractframework/entity": "0.12.2",
    "@abstractframework/note": "0.3.1",
    "@abstractframework/assistant": "0.2.2"
}

# Shared npm libraries are recorded separately from launchable browser apps.
NPM_LIBRARY_RELEASE_VERSIONS: dict[str, str] = {
    "@abstractframework/app-server": "0.1.13",
    "@abstractframework/ui-kit": "0.9.30",
    "@abstractframework/panel-chat": "0.9.15",
    "@abstractframework/monitor-active-memory": "0.2.2",
    "@abstractframework/monitor-flow": "0.1.10",
    "@abstractframework/monitor-gpu": "0.1.10",
    "@abstractframework/monitor-memory": "0.1.10"
}

# Terminal tools published on crates.io alongside this release (installed with `cargo install`,
# or by the bootstrap scripts: the gateway console and abstractcode by default). The installers
# never build `abstractcore-console` (0.7.1 decision): it is the console of a standalone
# `abstractcore serve`, and the gateway's terminal console already carries its Models and
# Engines screens; it is listed here as a release version only. `abstracttui` and `abstractavatar`
# are the libraries these tools build on (`abstracttui`'s `avatar` feature resolves
# `abstractavatar` from crates.io); they are release versions, not installed tools.
CRATE_RELEASE_VERSIONS: dict[str, str] = {
    "abstractgateway-console": "0.18.1",
    "abstractcore-console": "0.8.1",
    "abstractcode": "0.15.0",
    "abstracttui": "0.10.0",
    "abstractavatar": "0.2.0",
    "abstracttui-graph": "0.9.0",
    "abstracttui-mermaid": "0.9.0"
}

# The light profile installs plain `abstractcore` (no extra): AbstractCore's light setting already
# carries every remote provider, the tools, media and the capability plugins. The apple and gpu
# profiles get AbstractCore's local engines through the gateway's profile.
CORE_DEFAULT_EXTRAS: list[str] = []

# Metadata and CLI inspection must not initialize Core's user configuration.
# Resolve the convenience SDK exports only when the caller asks for them.
_CORE_REEXPORTS = frozenset({"GenerateResponse", "create_llm"})
__all__ = [
    "CORE_DEFAULT_EXTRAS",
    "RELEASE_VERSIONS",
    "GenerateResponse",
    "create_llm",
    "get_installed_packages",
    "get_release_profile",
    "print_status",
]


def __getattr__(name: str) -> Any:
    if name in _CORE_REEXPORTS:
        value = getattr(import_module("abstractcore"), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _CORE_REEXPORTS)


def get_release_profile() -> dict[str, object]:
    """Return the pinned global release profile shipped by this package."""

    return {
        "abstractframework": __version__,
        "packages": RELEASE_VERSIONS.copy(),
        "distributions": PACKAGE_DISTRIBUTIONS.copy(),
        "npm_packages": NPM_RELEASE_VERSIONS.copy(),
        "npm_libraries": NPM_LIBRARY_RELEASE_VERSIONS.copy(),
        "crates": CRATE_RELEASE_VERSIONS.copy(),
        "core_extras": list(CORE_DEFAULT_EXTRAS),
        "install_profiles": {
            "light": "pip install abstractframework",
            "apple": 'pip install "abstractframework[apple]"',
            "gpu": 'pip install "abstractframework[gpu]"',
        },
    }


def get_installed_packages() -> dict[str, str]:
    """Read installed distribution versions without importing component packages."""

    packages: dict[str, str] = {}

    for import_name, distribution in PACKAGE_DISTRIBUTIONS.items():
        try:
            packages[import_name] = version(distribution)
        except PackageNotFoundError:
            continue

    return packages


def print_status() -> None:
    """Print installation status of the main AbstractFramework Python packages."""

    installed = get_installed_packages()
    all_packages = list(PACKAGE_DISTRIBUTIONS)

    print("AbstractFramework installation status")
    print("=" * 40)

    for pkg in all_packages:
        if pkg in installed:
            print(f"  ✓ {pkg}: {installed[pkg]}")
        else:
            print(f"  ✗ {pkg}: not installed")

    print("")
    print(f"Installed: {len(installed)}/{len(all_packages)} packages")

    if len(installed) < len(all_packages):
        print("")
        print("To install the framework profile:")
        print("  pip install abstractframework")
        print("")
        print("Hardware-local profiles:")
        print('  pip install "abstractframework[apple]"')
        print('  pip install "abstractframework[gpu]"')
