"""
AbstractFramework (documentation index)

This package provides utilities to inspect which AbstractFramework packages are installed.

All functionality lives in the component projects (each has its own repository, PyPI package, docs, and release cadence).
Install individual packages as needed from PyPI.

Start here:
  - https://github.com/lpalbou/AbstractFramework#readme
  - https://github.com/lpalbou/AbstractFramework/blob/main/docs/getting-started.md
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Laurent-Philippe Albou"
__license__ = "MIT"

# Convenience re-exports (AbstractCore is a base dependency of this meta-package).
# Keep this import lightweight: do not import optional tool/media deps here.
try:
    from abstractcore import GenerateResponse, create_llm  # type: ignore

    __all__ = ["create_llm", "GenerateResponse"]
except Exception:  # pragma: no cover
    __all__ = []


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
        print('To install additional packages, see:')
        print('  https://github.com/lpalbou/AbstractFramework#install')
