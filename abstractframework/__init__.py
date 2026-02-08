"""
AbstractFramework unified distribution package.

This package provides:
- a single install entrypoint for the full AbstractFramework ecosystem
- lightweight helpers to inspect installed component versions

Most implementation functionality still lives in component projects.
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Laurent-Philippe Albou"
__license__ = "MIT"

RELEASE_VERSIONS: dict[str, str] = {
    "abstractcore": "2.11.8",
    "abstractruntime": "0.4.2",
    "abstractagent": "0.3.1",
    "abstractflow": "0.3.7",
    "abstractcode": "0.3.6",
    "abstractgateway": "0.2.1",
    "abstractmemory": "0.0.2",
    "abstractsemantics": "0.0.2",
    "abstractvoice": "0.6.3",
    "abstractvision": "0.2.1",
    "abstractassistant": "0.4.2",
}

CORE_DEFAULT_EXTRAS = [
    "openai",
    "anthropic",
    "huggingface",
    "embeddings",
    "tokens",
    "tools",
    "media",
    "compression",
    "server",
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
        "flow_extra": "editor",
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
        print("To install the full pinned framework:")
        print('  pip install "abstractframework==0.1.0"')
