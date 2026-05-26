from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _version_from_attr(path: Path) -> str:
    match = re.search(r'__version__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"))
    assert match is not None
    return match.group(1)


def test_framework_all_apple_pins_abstractvoice_all_apple() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    voice_version = _version_from_attr(ROOT / "abstractvoice" / "abstractvoice" / "_version.py")

    all_apple = pyproject["project"]["optional-dependencies"]["all-apple"]

    assert f"abstractvoice[all-apple]=={voice_version}" in all_apple


def test_macos_installer_full_and_voice_components_use_all_apple() -> None:
    manifest = json.loads((ROOT / "abstractinstallers" / "abstractframework-macos" / "manifest.local.json").read_text())
    components = {item["id"]: item for item in manifest["components"]}
    voice_version = _version_from_attr(ROOT / "abstractvoice" / "abstractvoice" / "_version.py")

    assert components["framework_full"]["extras"] == ["all-apple"]
    assert components["abstractvoice"]["extras"] == ["all-apple"]
    assert components["abstractvoice"]["version"] == voice_version
