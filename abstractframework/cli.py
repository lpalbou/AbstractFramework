"""Command line helpers for the AbstractFramework meta-package."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from . import PACKAGE_DISTRIBUTIONS, RELEASE_VERSIONS, __version__
from .install_manifest import check_install_manifest, manifest_json, write_install_manifest


STATUS_RANK = {"error": 2, "warn": 1, "ok": 0, "info": 0}

DEFAULT_GATEWAY_URL = "http://127.0.0.1:8080"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_LMSTUDIO_URL = "http://127.0.0.1:1234/v1"
SUPPORTED_PYTHON = ((3, 10), (3, 13))
MIN_NODE_MAJOR = 18
MIN_MACOS_MAJOR = 14
DISK_WARN_BYTES = 5 * 1024**3
DISK_ERROR_BYTES = 1 * 1024**3


@dataclass(frozen=True)
class Check:
    """One doctor finding. ``status`` is ok | warn | error | info (info never fails)."""

    id: str
    status: str
    message: str
    detail: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"id": self.id, "status": self.status, "message": self.message}
        if self.detail:
            out["detail"] = self.detail
        if self.data:
            out["data"] = self.data
        return out


def _distribution_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _command_version(command: str) -> str | None:
    executable = shutil.which(command)
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return "available"
    text = (result.stdout or result.stderr).strip().splitlines()
    return text[0] if text else "available"


def _http_get_json(url: str, timeout: float) -> tuple[int | None, Any, str | None]:
    """Read-only GET. Returns (status, parsed JSON or None, error)."""

    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            body = response.read(1_000_000)
            try:
                return response.status, json.loads(body.decode("utf-8")), None
            except (ValueError, UnicodeDecodeError):
                return response.status, None, None
    except urllib.error.HTTPError as exc:
        return exc.code, None, f"HTTP {exc.code}"
    except Exception as exc:  # connection refused, timeout, DNS ...
        reason = getattr(exc, "reason", exc)
        return None, None, str(reason)


def _uv_tool_bin_dir() -> Path:
    for env in ("UV_TOOL_BIN_DIR", "XDG_BIN_HOME"):
        value = os.environ.get(env)
        if value:
            return Path(value)
    return Path.home() / ".local" / "bin"


def _find_executable(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    suffix = ".exe" if platform.system() == "Windows" else ""
    candidate = _uv_tool_bin_dir() / f"{name}{suffix}"
    return str(candidate) if candidate.exists() else None


def _parse_major(version_text: str | None) -> int | None:
    if not version_text:
        return None
    match = re.search(r"(\d+)(?:\.\d+)*", version_text)
    return int(match.group(1)) if match else None


def _macos_version() -> tuple[int, ...] | None:
    if platform.system() != "Darwin":
        return None
    raw = platform.mac_ver()[0]
    try:
        return tuple(int(part) for part in raw.split(".") if part)
    except ValueError:
        return None


def _gateway_url() -> str:
    return (os.environ.get("ABSTRACTGATEWAY_URL") or DEFAULT_GATEWAY_URL).rstrip("/")


def _ollama_url() -> str:
    raw = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST") or DEFAULT_OLLAMA_URL
    if "://" not in raw:
        raw = f"http://{raw}"
    return raw.rstrip("/")


def _lmstudio_url() -> str:
    raw = (os.environ.get("LMSTUDIO_BASE_URL") or DEFAULT_LMSTUDIO_URL).rstrip("/")
    return raw if raw.endswith("/v1") else f"{raw}/v1"


def _python_check() -> Check:
    version = ".".join(str(part) for part in sys.version_info[:3])
    low, high = SUPPORTED_PYTHON
    data = {"version": version, "executable": sys.executable, "supported": "3.10-3.13"}
    if sys.version_info[:2] < low:
        return Check("python", "error", f"Python {version} is below the supported 3.10", data=data)
    if sys.version_info[:2] > high:
        return Check(
            "python",
            "warn",
            f"Python {version} is newer than the tested 3.10-3.13",
            "The bootstrap installs the framework on Python 3.12 through uv.",
            data=data,
        )
    return Check("python", "ok", f"Python {version} (supported: 3.10-3.13)", data=data)


def _platform_checks() -> list[Check]:
    system = platform.system()
    machine = platform.machine().lower()
    checks: list[Check] = []
    macos = _macos_version()
    data: dict[str, Any] = {"os": system, "arch": machine}
    if macos:
        data["macos"] = ".".join(str(part) for part in macos)
    if system == "Darwin" and machine in {"arm64", "aarch64"}:
        if macos and macos[0] >= MIN_MACOS_MAJOR:
            checks.append(
                Check(
                    "profile:apple",
                    "ok",
                    f"Apple Silicon on macOS {data.get('macos')}: the apple profile is supported",
                    data=data,
                )
            )
        else:
            checks.append(
                Check(
                    "profile:apple",
                    "warn",
                    f"The apple profile needs macOS {MIN_MACOS_MAJOR}+ (this is {data.get('macos')})",
                    "Use the light profile, or upgrade macOS for local MLX engines.",
                    data=data,
                )
            )
    elif system == "Darwin":
        checks.append(
            Check("profile:apple", "info", "Intel Mac: use the light profile", data=data)
        )
    else:
        checks.append(
            Check("profile:apple", "info", "The apple profile is for Apple Silicon Macs", data=data)
        )

    gpu_tool = None
    for tool in ("nvidia-smi", "rocminfo"):
        if shutil.which(tool):
            gpu_tool = tool
            break
    if gpu_tool:
        checks.append(
            Check("profile:gpu", "ok", f"{gpu_tool} is available", data={"tool": gpu_tool})
        )
    else:
        checks.append(
            Check(
                "profile:gpu",
                "info",
                "No nvidia-smi or rocminfo; the gpu profile would run local engines on CPU",
            )
        )
    return checks


def _tool_checks() -> list[Check]:
    checks: list[Check] = []
    uv = _find_executable("uv")
    if uv:
        version = _command_version(uv)
        checks.append(Check("uv", "ok", f"uv is available: {version}", data={"path": uv}))
    else:
        checks.append(
            Check(
                "uv",
                "warn",
                "uv is not installed",
                "The bootstrap (scripts/install.sh, install.ps1) installs it; see docs/install.md.",
            )
        )

    node = _find_executable("node")
    node_version = _command_version(node) if node else None
    major = _parse_major(node_version)
    npm = _find_executable("npm")
    node_data: dict[str, Any] = {"path": node, "version": node_version, "npm": npm}
    if node and major is not None and major >= MIN_NODE_MAJOR:
        source = "nodejs-wheel (uv tool)" if str(_uv_tool_bin_dir()) in node else "system"
        node_data["source"] = source
        checks.append(Check("node", "ok", f"Node {node_version} ({source})", data=node_data))
    elif node:
        checks.append(
            Check(
                "node",
                "warn",
                f"Node {node_version} is older than {MIN_NODE_MAJOR}; the browser apps need 18+",
                "Install a newer Node, or run: uv tool install nodejs-wheel",
                data=node_data,
            )
        )
    else:
        checks.append(
            Check(
                "node",
                "warn",
                "Node is not available; the browser apps (npx) need Node 18+",
                "No admin needed: uv tool install nodejs-wheel (or install.sh --with-apps)",
            )
        )
    return checks


def _disk_check() -> Check:
    target = Path.home()
    try:
        usage = shutil.disk_usage(target)
    except OSError as exc:
        return Check("disk", "warn", f"Could not read free disk space for {target}: {exc}")
    free_gb = usage.free / 1024**3
    data = {"path": str(target), "free_bytes": usage.free}
    if usage.free < DISK_ERROR_BYTES:
        return Check("disk", "error", f"Only {free_gb:.1f} GB free under {target}", data=data)
    if usage.free < DISK_WARN_BYTES:
        return Check(
            "disk",
            "warn",
            f"{free_gb:.1f} GB free under {target}; local models need several GB each",
            data=data,
        )
    return Check("disk", "ok", f"{free_gb:.1f} GB free under {target}", data=data)


def _gateway_checks(timeout: float) -> list[Check]:
    """Read-only probes of the gateway (GET /api/health) and its local config."""

    checks: list[Check] = []
    url = _gateway_url()
    status, body, error = _http_get_json(f"{url}/api/health", timeout)
    data: dict[str, Any] = {"url": url}
    if status == 200 and isinstance(body, dict) and body.get("service") == "abstractgateway":
        data["health"] = body.get("status")
        checks.append(Check("gateway", "ok", f"Gateway reachable at {url} ({body.get('status')})",
                            f"Console: {url}/console", data=data))
    elif status is not None:
        data["http_status"] = status
        checks.append(Check("gateway", "warn", f"{url}/api/health answered {status}, not a gateway",
                            data=data))
    else:
        data["error"] = error
        checks.append(
            Check(
                "gateway",
                "warn",
                f"No gateway at {url}",
                "Start it with `abstractgateway serve --host 127.0.0.1 --port 8080` or "
                "re-run the bootstrap; set ABSTRACTGATEWAY_URL for another address.",
                data=data,
            )
        )

    config_cli = _find_executable("abstractgateway-config")
    if not config_cli:
        checks.append(Check("gateway:config", "info", "abstractgateway-config is not on PATH"))
        return checks
    try:
        result = subprocess.run(
            [config_cli, "status", "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=max(timeout, 30.0),
        )
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
    except Exception as exc:
        checks.append(Check("gateway:config", "warn", f"abstractgateway-config status failed: {exc}"))
        return checks
    gateway = payload.get("gateway") if isinstance(payload, dict) else None
    gateway = gateway if isinstance(gateway, dict) else {}
    summary = {
        "data_dir": gateway.get("data_dir"),
        "auth_configured": gateway.get("auth_configured"),
        "auth_mode": gateway.get("auth_mode"),
        "store_backend": gateway.get("store_backend"),
        "service": payload.get("service") if isinstance(payload, dict) else None,
    }
    if result.returncode != 0 or not gateway:
        checks.append(
            Check("gateway:config", "warn", "abstractgateway-config status --json gave no gateway section",
                  data={k: v for k, v in summary.items() if v is not None})
        )
    else:
        checks.append(
            Check(
                "gateway:config",
                "ok",
                f"Gateway data dir: {summary['data_dir']}",
                data={k: v for k, v in summary.items() if v is not None},
            )
        )
    return checks


def _engine_checks(timeout: float) -> list[Check]:
    checks: list[Check] = []
    ollama = _ollama_url()
    status, body, error = _http_get_json(f"{ollama}/api/version", timeout)
    if status == 200:
        version = body.get("version") if isinstance(body, dict) else None
        label = f"Ollama {version}" if version else "Ollama"
        checks.append(Check("engine:ollama", "ok", f"{label} reachable at {ollama}",
                            data={"url": ollama, "version": version}))
    else:
        checks.append(Check("engine:ollama", "info", f"Ollama not reachable at {ollama} (optional)",
                            data={"url": ollama, "error": error or f"HTTP {status}"}))
    lmstudio = _lmstudio_url()
    status, body, error = _http_get_json(f"{lmstudio}/models", timeout)
    if status == 200:
        models = body.get("data") if isinstance(body, dict) else None
        count = len(models) if isinstance(models, list) else None
        checks.append(Check("engine:lmstudio", "ok", f"LM Studio reachable at {lmstudio}",
                            data={"url": lmstudio, "models": count}))
    else:
        checks.append(Check("engine:lmstudio", "info", f"LM Studio not reachable at {lmstudio} (optional)",
                            data={"url": lmstudio, "error": error or f"HTTP {status}"}))
    return checks


def build_doctor_report(
    include_environment: bool = True,
    include_network: bool | None = None,
    timeout: float = 2.0,
) -> dict[str, object]:
    """Return a doctor report without importing heavy local inference stacks.

    Network probes are read-only GETs (gateway ``/api/health``, Ollama ``/api/version``,
    LM Studio ``/v1/models``); they run with the environment checks unless disabled.
    """

    if include_network is None:
        include_network = include_environment
    checks: list[Check] = [_python_check()]

    installed_framework = _distribution_version("abstractframework")
    if installed_framework in {None, __version__}:
        status = "ok" if installed_framework == __version__ else "warn"
        message = (
            f"abstractframework {installed_framework} matches release profile"
            if installed_framework
            else "abstractframework distribution metadata is not installed"
        )
        checks.append(Check("abstractframework", status, message))
    else:
        checks.append(
            Check(
                "abstractframework",
                "error",
                f"abstractframework {installed_framework} does not match {__version__}",
            )
        )

    for package_id, expected in RELEASE_VERSIONS.items():
        distribution = PACKAGE_DISTRIBUTIONS[package_id]
        actual = _distribution_version(distribution)
        if actual is None:
            checks.append(
                Check(
                    f"package:{package_id}",
                    "error",
                    f"{distribution} is not installed",
                    f"Expected {distribution}=={expected}",
                )
            )
        elif actual == expected:
            checks.append(Check(f"package:{package_id}", "ok", f"{distribution}=={actual}"))
        else:
            checks.append(
                Check(
                    f"package:{package_id}",
                    "error",
                    f"{distribution}=={actual} does not match pinned {expected}",
                )
            )

    if include_environment:
        checks.extend(_platform_checks())
        checks.extend(_tool_checks())
        checks.append(_disk_check())
    if include_network:
        checks.extend(_gateway_checks(timeout))
        checks.extend(_engine_checks(timeout))

    worst = max((STATUS_RANK[check.status] for check in checks), default=0)
    status = "error" if worst == 2 else "warn" if worst == 1 else "ok"
    return {
        "schema": "abstractframework_doctor_v2",
        "abstractframework": __version__,
        "status": status,
        "platform": {
            "os": platform.system(),
            "arch": platform.machine(),
            "python": ".".join(str(part) for part in sys.version_info[:3]),
        },
        "checks": [check.as_dict() for check in checks],
    }


def _print_doctor(report: dict[str, object]) -> None:
    print(f"AbstractFramework doctor ({report['status']})")
    print("=" * 40)
    for raw in report["checks"]:  # type: ignore[index]
        check = raw  # type: ignore[assignment]
        marker = {"ok": "OK", "warn": "WARN", "error": "ERROR", "info": "INFO"}[check["status"]]
        print(f"[{marker}] {check['message']}")
        if check.get("detail"):
            print(f"       {check['detail']}")


def _doctor(args: argparse.Namespace) -> int:
    report = build_doctor_report(
        include_environment=not args.no_environment,
        include_network=not (args.no_environment or args.no_network),
        timeout=args.timeout,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_doctor(report)
    return 1 if report["status"] == "error" else 0


def _manifest(args: argparse.Namespace) -> int:
    if args.write:
        write_install_manifest(args.write)
        print(f"Wrote {args.write}")
        return 0
    if args.check:
        ok, message = check_install_manifest(args.check)
        print(message)
        return 0 if ok else 1
    print(manifest_json(), end="")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="abstractframework")
    subparsers = parser.add_subparsers(dest="command")

    doctor = subparsers.add_parser("doctor", help="Check install health and profile consistency")
    doctor.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    doctor.add_argument(
        "--no-environment",
        action="store_true",
        help="Skip host, tool and network probes; only check the Python package profile",
    )
    doctor.add_argument(
        "--no-network",
        action="store_true",
        help="Skip the read-only HTTP probes (gateway /api/health, Ollama, LM Studio)",
    )
    doctor.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Seconds per HTTP probe (default: 2)",
    )
    doctor.set_defaults(func=_doctor)

    manifest = subparsers.add_parser("manifest", help="Print or validate the install manifest")
    manifest.add_argument("--write", type=Path, help="Write the generated manifest to a path")
    manifest.add_argument("--check", type=Path, help="Check a manifest file against the generator")
    manifest.set_defaults(func=_manifest)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
