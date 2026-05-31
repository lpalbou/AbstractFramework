"""Generated install manifest helpers for AbstractFramework."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import NPM_RELEASE_VERSIONS, PACKAGE_DISTRIBUTIONS, RELEASE_VERSIONS, __version__

MANIFEST_SCHEMA_VERSION = 1
MINIMUM_INSTALLER_VERSION = "0.1.0"


def _python_packages() -> list[dict[str, str]]:
    return [
        {
            "id": package_id,
            "distribution": PACKAGE_DISTRIBUTIONS[package_id],
            "version": version,
            "registry": "pypi",
        }
        for package_id, version in RELEASE_VERSIONS.items()
    ]


def _npm_apps() -> list[dict[str, str]]:
    return [
        {
            "id": package_name.rsplit("/", 1)[-1],
            "package": package_name,
            "version": version,
            "registry": "npm",
            "command": f"npx {package_name}",
        }
        for package_name, version in NPM_RELEASE_VERSIONS.items()
    ]


def build_install_manifest() -> dict[str, Any]:
    """Build the installer-consumable manifest from root release pins."""

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "minimum_installer_version": MINIMUM_INSTALLER_VERSION,
        "framework": {
            "id": "abstractframework",
            "name": "AbstractFramework",
            "distribution": "abstractframework",
            "version": __version__,
            "registry": "pypi",
            "python_requires": ">=3.10",
        },
        "source": {
            "repository": "https://github.com/lpalbou/AbstractFramework",
            "release_profile": "abstractframework.RELEASE_VERSIONS",
        },
        "profiles": [
            {
                "id": "light",
                "name": "Light",
                "summary": (
                    "Remote-first install. Full framework functionality is available through "
                    "remote or OpenAI-compatible endpoints; no local MLX, CUDA, Diffusers, or "
                    "model-runtime stacks are installed by this profile."
                ),
                "pip_requirements": [f"abstractframework=={__version__}"],
                "local_inference": False,
                "platforms": ["macos", "linux", "windows"],
                "prerequisites": ["python>=3.10", "network"],
                "best_for": [
                    "cloud APIs",
                    "LM Studio, Ollama, vLLM, llama.cpp, or other endpoint servers",
                    "lowest-friction install",
                ],
                "excludes": ["local MLX engines", "local CUDA/ROCm engines"],
            },
            {
                "id": "apple",
                "name": "Apple",
                "summary": (
                    "Native Apple Silicon profile. Adds local MLX/Metal-capable stacks on top "
                    "of the same framework interfaces and endpoint providers."
                ),
                "pip_requirements": [f"abstractframework[apple]=={__version__}"],
                "local_inference": True,
                "platforms": ["macos"],
                "prerequisites": ["python>=3.10", "apple-silicon", "network"],
                "best_for": ["Mac users who want local Apple Silicon inferencers"],
                "excludes": ["CUDA/ROCm engines"],
            },
            {
                "id": "gpu",
                "name": "GPU",
                "summary": (
                    "Native GPU profile. Adds CUDA/ROCm-oriented local stacks on top of the "
                    "same framework interfaces and endpoint providers."
                ),
                "pip_requirements": [f"abstractframework[gpu]=={__version__}"],
                "local_inference": True,
                "platforms": ["linux", "windows"],
                "prerequisites": ["python>=3.10", "gpu-driver", "network"],
                "best_for": ["workstations or servers with supported discrete GPUs"],
                "excludes": ["Apple MLX-only engines"],
            },
        ],
        "python_packages": _python_packages(),
        "npm_apps": _npm_apps(),
        "post_install": {
            "doctor": ["abstractframework", "doctor"],
            "core_config": ["abstractcore", "--config"],
            "gateway_flow": {
                "gateway": ["abstractgateway", "serve"],
                "flow": ["npx", "@abstractframework/flow"],
            },
        },
        "security": {
            "secrets_in_manifest": False,
            "native_artifacts_signed": False,
            "notes": "Prototype manifest; production installer artifacts must add signatures.",
        },
    }


def manifest_json(indent: int = 2) -> str:
    """Return the install manifest as stable JSON."""

    return json.dumps(build_install_manifest(), indent=indent, sort_keys=True) + "\n"


def write_install_manifest(path: str | Path) -> None:
    """Write the generated install manifest to a path."""

    Path(path).write_text(manifest_json(), encoding="utf-8")


def check_install_manifest(path: str | Path) -> tuple[bool, str]:
    """Compare a checked-in manifest file with the generated manifest."""

    manifest_path = Path(path)
    expected = manifest_json()
    actual = manifest_path.read_text(encoding="utf-8")
    if actual == expected:
        return True, f"{manifest_path} is up to date"
    return False, f"{manifest_path} differs from generated AbstractFramework install manifest"
