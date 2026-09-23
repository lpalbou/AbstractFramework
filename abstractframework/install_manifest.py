"""Generated install manifest helpers for AbstractFramework."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import NPM_RELEASE_VERSIONS, PACKAGE_DISTRIBUTIONS, RELEASE_VERSIONS, __version__

MANIFEST_SCHEMA_VERSION = 2
MINIMUM_INSTALLER_VERSION = "0.2.0"

REPOSITORY = "https://github.com/lpalbou/AbstractFramework"
RAW_SCRIPTS = "https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts"

# Python version the bootstrap provisions through uv. 3.12 satisfies MLX, F5-TTS (3.11+)
# and vLLM (3.10-3.13); it is passed explicitly because the packages have no upper bound.
BOOTSTRAP_PYTHON = "3.12"
DEFAULT_GATEWAY_PORT = 8080

# Flags shared by scripts/install.sh (POSIX) and scripts/install.ps1 (PowerShell).
BOOTSTRAP_FLAGS: list[dict[str, str]] = [
    {"sh": "--profile auto|light|apple|gpu", "ps": "-Profile", "env": "AF_PROFILE",
     "summary": "Install profile; auto picks apple on Apple Silicon macOS 14+, gpu when "
                "nvidia-smi/rocminfo works, light otherwise."},
    {"sh": "--port N", "ps": "-Port", "env": "AF_PORT",
     "summary": "Gateway port (default 8080; the next free port when 8080 is busy)."},
    {"sh": "--pin VERSION|latest", "ps": "-Pin", "env": "AF_PIN",
     "summary": "abstractgateway version (default: bootstrap.gateway_version)."},
    {"sh": "--from PATH|REQUIREMENT", "ps": "-From", "env": "AF_FROM",
     "summary": "Install the gateway from a checkout, wheel or requirement (testing)."},
    {"sh": "--data-dir DIR", "ps": "-DataDir", "env": "AF_DATA_DIR",
     "summary": "Gateway data dir (default: the per-OS user data dir)."},
    {"sh": "--with-apps", "ps": "-WithApps", "env": "",
     "summary": "Ensure Node.js >= 18 for the npx browser apps (uv tool install nodejs-wheel)."},
    {"sh": "--with-console", "ps": "-WithConsole", "env": "",
     "summary": "cargo install abstractgateway-console when cargo exists."},
    {"sh": "--with-code-cli", "ps": "-WithCodeCli", "env": "",
     "summary": "cargo install abstractcode (terminal client) when cargo exists."},
    {"sh": "--with-core-cli", "ps": "-WithCoreCli", "env": "",
     "summary": "Also expose the abstractcore command (--with-executables-from abstractcore)."},
    {"sh": "--with-ollama", "ps": "-WithOllama", "env": "",
     "summary": "Run Ollama's official installer (Linux/macOS may ask for sudo)."},
    {"sh": "--with-lmstudio", "ps": "-WithLmStudio", "env": "",
     "summary": "Install LM Studio (headless llmster on macOS/Linux, winget on Windows)."},
    {"sh": "--no-tray", "ps": "-NoTray", "env": "", "summary": "Skip the tray extra."},
    {"sh": "--no-service", "ps": "-NoService", "env": "",
     "summary": "Do not register a login service; start the gateway in the background."},
    {"sh": "--no-start", "ps": "-NoStart", "env": "", "summary": "Install only."},
    {"sh": "--no-open", "ps": "-NoOpen", "env": "", "summary": "Do not open the browser."},
    {"sh": "--print", "ps": "-Print", "env": "",
     "summary": "Dry run: preflight, then print every command; change nothing."},
    {"sh": "--uninstall [--purge]", "ps": "-Uninstall [-Purge]", "env": "",
     "summary": "Remove the service and uv tools (purge also deletes the data dir)."},
]


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
                "prerequisites": ["python>=3.10", "apple-silicon", "macos>=14", "network"],
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
        "bootstrap": _bootstrap(),
        "post_install": _post_install(),
        "security": {
            "secrets_in_manifest": False,
            "native_artifacts_signed": False,
            "notes": (
                "The bootstrap is a script (curl | sh, irm | iex) that installs signed-by-vendor "
                "or PyPI/npm artifacts; nothing it runs needs our code signature. Only native "
                "double-click apps (AbstractAssistant .app, future launchers) need signing."
            ),
        },
    }


def _bootstrap() -> dict[str, Any]:
    gateway_version = RELEASE_VERSIONS["abstractgateway"]
    return {
        "gateway_version": gateway_version,
        "python": BOOTSTRAP_PYTHON,
        "tool_requirement": "abstractgateway[{extras}]==" + gateway_version,
        "profile_extras": {"light": [], "apple": ["apple"], "gpu": ["gpu"]},
        "optional_extras": ["tray"],
        "default_port": DEFAULT_GATEWAY_PORT,
        "scripts": {
            "unix": {
                "url": f"{RAW_SCRIPTS}/install.sh",
                "platforms": ["macos", "linux"],
                "one_liner": f"curl -LsSf {RAW_SCRIPTS}/install.sh | sh",
                "with_flags": f"curl -LsSf {RAW_SCRIPTS}/install.sh | sh -s -- --with-apps",
            },
            "windows": {
                "url": f"{RAW_SCRIPTS}/install.ps1",
                "platforms": ["windows"],
                "one_liner": (
                    'powershell -ExecutionPolicy ByPass -c "irm '
                    f'{RAW_SCRIPTS}/install.ps1 | iex"'
                ),
                "with_flags": (
                    "& ([scriptblock]::Create((irm "
                    f"{RAW_SCRIPTS}/install.ps1))) -WithApps"
                ),
            },
        },
        "flags": BOOTSTRAP_FLAGS,
        "steps": [
            "preflight (OS, arch, macOS >= 14 for apple, GPU driver for gpu, disk, port)",
            "install uv when missing (astral.sh official script, no admin)",
            f"uv python install {BOOTSTRAP_PYTHON}",
            f'uv tool install --python {BOOTSTRAP_PYTHON} "abstractgateway[<extras>]==<pin>"',
            "optional: nodejs-wheel, cargo crates, Ollama / LM Studio vendor installers",
            "abstractgateway service install (when supported) or a background start",
            "wait for GET /api/health",
            "abstractgateway-config claim-url (when supported) and open /console",
        ],
        "uninstall": [
            ["abstractgateway", "service", "uninstall"],
            ["uv", "tool", "uninstall", "abstractgateway"],
        ],
    }


def _post_install() -> dict[str, Any]:
    base_url = f"http://127.0.0.1:{DEFAULT_GATEWAY_PORT}"
    return {
        "entrypoint": "console",
        "gateway": [
            "abstractgateway",
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            str(DEFAULT_GATEWAY_PORT),
        ],
        "health_url": f"{base_url}/api/health",
        "console_url": f"{base_url}/console",
        "claim": ["abstractgateway-config", "claim-url"],
        "claim_fallback": {
            "token_file": "<data_dir>/auth/bootstrap-admin-token",
            "command": ["abstractgateway-config", "bootstrap-admin", "--print-token"],
        },
        "service": ["abstractgateway", "service", "install"],
        "doctor": ["abstractframework", "doctor"],
        "apps": [["npx", "-y", package] for package in NPM_RELEASE_VERSIONS],
        "notes": (
            "Providers, API keys, engines, models and users are configured in the gateway "
            "console (/console first-run wizard); every console action prints its CLI twin."
        ),
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
