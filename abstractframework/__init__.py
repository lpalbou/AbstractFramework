"""
AbstractFramework unified distribution package.

This package provides:
- a single install entrypoint for the full AbstractFramework ecosystem
- lightweight helpers to inspect installed component versions

Most implementation functionality still lives in component projects.
"""

from __future__ import annotations

__version__ = "0.1.6"
__author__ = "Laurent-Philippe Albou"
__license__ = "MIT"

RELEASE_VERSIONS: dict[str, str] = {
    "abstractcore": "2.13.31",
    "abstractruntime": "0.4.26",
    "abstractagent": "0.3.10",
    "abstractflow": "0.3.17",
    "abstractcode": "0.3.8",
    "abstractgateway": "0.2.22",
    "abstractmemory": "0.2.6",
    "abstractsemantics": "0.0.4",
    "abstractvoice": "0.10.17",
    "abstractvision": "0.3.18",
    "abstractmusic": "0.1.12",
    "abstractassistant": "0.4.8",
}

CORE_DEFAULT_EXTRAS = [
    "remote",
    "tools",
    "media",
    "vision",
    "voice",
    "audio",
    "music",
]

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
        "core_extras": list(CORE_DEFAULT_EXTRAS),
        "install_profiles": {
            "base": "pip install abstractframework",
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

    for name in [
        "abstractcore",
        "abstractruntime",
        "abstractagent",
        "abstractflow",
        "abstractcode",
        "abstractgateway",
        "abstractmemory",
        "abstractsemantics",
        "abstractvoice",
        "abstractvision",
        "abstractmusic",
        "abstractassistant",
    ]:
        _maybe_add(name)

    return packages


def print_status() -> None:
    """Print installation status of the main AbstractFramework Python packages."""

    installed = get_installed_packages()
    all_packages = [
        "abstractcore",
        "abstractruntime",
        "abstractagent",
        "abstractflow",
        "abstractcode",
        "abstractgateway",
        "abstractmemory",
        "abstractsemantics",
        "abstractvoice",
        "abstractvision",
        "abstractmusic",
        "abstractassistant",
    ]

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
