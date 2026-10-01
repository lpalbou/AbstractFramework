"""
AbstractFramework unified distribution package.

This package provides:
- a single install entrypoint for the full AbstractFramework ecosystem
- lightweight helpers to inspect installed component versions

Most implementation functionality still lives in component projects.
"""

from __future__ import annotations

__version__ = "0.8.0"
__author__ = "Laurent-Philippe Albou"
__license__ = "MIT"

RELEASE_VERSIONS: dict[str, str] = {
    "abstractcore": "2.22.0",
    "abstractruntime": "0.8.2",
    "abstractagent": "0.3.17",
    "abstractgateway": "0.10.0",
    "abstractskill": "0.3.0",
    "abstractmemory": "0.3.0",
    "abstractsemantics": "0.0.5",
    "abstractvoice": "0.13.2",
    "abstractvision": "0.3.33",
    "abstractmusic": "0.1.15",
    "abstract3d": "0.3.2",
    "abstractassistant": "0.11.0",
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
}

NPM_RELEASE_VERSIONS: dict[str, str] = {
    "@abstractframework/flow": "0.6.0",
    "@abstractframework/code": "0.9.0",
    "@abstractframework/observer": "0.5.0",
    "@abstractframework/continuum": "0.6.0",
    "@abstractframework/entity": "0.5.0",
}

# Terminal tools published on crates.io alongside this release (installed with `cargo install`,
# or by the bootstrap scripts: the gateway console and abstractcode by default). The installers
# never build `abstractcore-console` (0.7.1 decision): it is the console of a standalone
# `abstractcore serve`, and the gateway's terminal console already carries its Models and
# Engines screens; it is listed here as a release version only.
CRATE_RELEASE_VERSIONS: dict[str, str] = {
    "abstractgateway-console": "0.13.0",
    "abstractcore-console": "0.6.0",
    "abstractcode": "0.8.0",
    "abstracttui": "0.6.0",
}

# The light profile installs plain `abstractcore` (no extra): AbstractCore's light setting already
# carries every remote provider, the tools, media and the capability plugins. The apple and gpu
# profiles get AbstractCore's local engines through the gateway's profile.
CORE_DEFAULT_EXTRAS: list[str] = []

# Convenience re-exports (AbstractCore is a base dependency of this meta-package).
# Keep this import lightweight: do not import optional tool/media deps here.
try:
    from abstractcore import GenerateResponse, create_llm  # type: ignore

    __all__ = [
        "CORE_DEFAULT_EXTRAS",
        "RELEASE_VERSIONS",
        "GenerateResponse",
        "create_llm",
        "get_installed_packages",
        "get_release_profile",
        "print_status",
    ]
except Exception:  # pragma: no cover
    __all__ = [
        "CORE_DEFAULT_EXTRAS",
        "RELEASE_VERSIONS",
        "get_installed_packages",
        "get_release_profile",
        "print_status",
    ]


def get_release_profile() -> dict[str, object]:
    """Return the pinned global release profile shipped by this package."""

    return {
        "abstractframework": __version__,
        "packages": RELEASE_VERSIONS.copy(),
        "distributions": PACKAGE_DISTRIBUTIONS.copy(),
        "npm_packages": NPM_RELEASE_VERSIONS.copy(),
        "crates": CRATE_RELEASE_VERSIONS.copy(),
        "core_extras": list(CORE_DEFAULT_EXTRAS),
        "install_profiles": {
            "light": "pip install abstractframework",
            "apple": 'pip install "abstractframework[apple]"',
            "gpu": 'pip install "abstractframework[gpu]"',
        },
    }


def get_installed_packages() -> dict[str, str]:
    """Return a dict of installed AbstractFramework Python packages and versions."""

    packages: dict[str, str] = {}

    def _maybe_add(import_name: str) -> None:
        try:
            mod = __import__(import_name)
            packages[import_name] = getattr(mod, "__version__", "installed")
        except Exception:
            return

    for name in PACKAGE_DISTRIBUTIONS:
        _maybe_add(name)

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
