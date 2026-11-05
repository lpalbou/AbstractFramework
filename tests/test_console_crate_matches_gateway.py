"""The terminal console this release installs is the one the pinned gateway release shipped.

AbstractGateway releases its terminal console (`console-tui/`, crate `abstractgateway-console`) with each gateway
version. The root pins both: `RELEASE_VERSIONS["abstractgateway"]` and
`CRATE_RELEASE_VERSIONS["abstractgateway-console"]` (which the installers build, see test_install_profiles). This
test reads `console-tui/Cargo.toml` at the gateway's release tag `v<gateway pin>`: from the sibling checkout when it
holds that tag, else from GitHub. It fails, never skips, when it cannot read it: a candidate that cannot prove its
console matches its gateway is not a candidate.
"""

from __future__ import annotations

import re
import subprocess
import urllib.request
from pathlib import Path

import pytest

from abstractframework import CRATE_RELEASE_VERSIONS, RELEASE_VERSIONS

ROOT = Path(__file__).resolve().parents[1]
RAW = "https://raw.githubusercontent.com/lpalbou/AbstractGateway/{tag}/console-tui/Cargo.toml"


def _shipped_console_cargo_toml(tag: str) -> str:
    sibling = ROOT / "abstractgateway"
    if (sibling / ".git").exists():
        got = subprocess.run(["git", "-C", str(sibling), "show", f"{tag}:console-tui/Cargo.toml"],
                             capture_output=True, text=True)
        if got.returncode == 0:
            return got.stdout
    try:
        with urllib.request.urlopen(RAW.format(tag=tag), timeout=30) as response:
            return response.read().decode("utf-8")
    except Exception as exc:  # noqa: BLE001 - any failure to read is a failure of the check
        pytest.fail(f"cannot read console-tui/Cargo.toml at AbstractGateway {tag} (sibling checkout or GitHub): {exc}")


def _package_version(cargo_toml: str) -> tuple[str, str]:
    package = cargo_toml.split("[package]", 1)[1].split("\n[", 1)[0]
    name = re.search(r'(?m)^\s*name\s*=\s*"([^"]+)"', package)
    version = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', package)
    assert name and version, "console-tui/Cargo.toml has no [package] name/version"
    return name.group(1), version.group(1)


def test_the_console_crate_pin_is_the_console_the_pinned_gateway_shipped() -> None:
    tag = f"v{RELEASE_VERSIONS['abstractgateway']}"
    name, shipped = _package_version(_shipped_console_cargo_toml(tag))
    assert name == "abstractgateway-console"
    pinned = CRATE_RELEASE_VERSIONS["abstractgateway-console"]
    assert pinned == shipped, (
        f"CRATE_RELEASE_VERSIONS pins abstractgateway-console {pinned}, but AbstractGateway {tag} ships "
        f"console-tui {shipped}: pin {shipped} (CRATE_RELEASE_VERSIONS, AF_CRATE_CONSOLE in both installers, docs)"
    )
