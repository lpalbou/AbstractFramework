"""Command line helpers for the AbstractFramework meta-package."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from . import PACKAGE_DISTRIBUTIONS, RELEASE_VERSIONS, __version__
from .install_manifest import check_install_manifest, manifest_json, write_install_manifest


@dataclass(frozen=True)
class Check:
    id: str
    status: str
    message: str
    detail: str | None = None

    def as_dict(self) -> dict[str, str]:
        data = {"id": self.id, "status": self.status, "message": self.message}
        if self.detail:
            data["detail"] = self.detail
        return data


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


def build_doctor_report(include_environment: bool = True) -> dict[str, object]:
    """Return a doctor report without importing heavy local inference stacks."""

    checks: list[Check] = []

    python_version = ".".join(str(part) for part in sys.version_info[:3])
    if sys.version_info >= (3, 10):
        checks.append(Check("python", "ok", f"Python {python_version} satisfies >=3.10"))
    else:
        checks.append(Check("python", "error", f"Python {python_version} is below required >=3.10"))

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
        node_version = _command_version("node")
        npm_version = _command_version("npm")
        if node_version:
            checks.append(Check("node", "ok", f"Node is available: {node_version}"))
        else:
            checks.append(Check("node", "warn", "Node is not available; browser UIs need Node/npm"))
        if npm_version:
            checks.append(Check("npm", "ok", f"npm is available: {npm_version}"))
        else:
            checks.append(Check("npm", "warn", "npm is not available; browser UIs need npm/npx"))

        system = platform.system()
        machine = platform.machine().lower()
        if system == "Darwin" and machine in {"arm64", "aarch64"}:
            checks.append(Check("hardware:apple", "ok", "Apple Silicon local profile can be used"))
        elif system == "Darwin":
            checks.append(
                Check("hardware:apple", "warn", "Apple local profile expects Apple Silicon")
            )
        else:
            checks.append(Check("hardware:apple", "warn", "Apple local profile is macOS-only"))

        if shutil.which("nvidia-smi"):
            checks.append(Check("hardware:gpu", "ok", "nvidia-smi is available"))
        else:
            checks.append(
                Check(
                    "hardware:gpu",
                    "warn",
                    "No nvidia-smi found; GPU profile may still work with another supported stack",
                )
            )

    status_rank = {"error": 2, "warn": 1, "ok": 0}
    worst = max((status_rank[check.status] for check in checks), default=0)
    status = "error" if worst == 2 else "warn" if worst == 1 else "ok"
    return {
        "abstractframework": __version__,
        "status": status,
        "checks": [check.as_dict() for check in checks],
    }


def _print_doctor(report: dict[str, object]) -> None:
    print(f"AbstractFramework doctor ({report['status']})")
    print("=" * 40)
    for raw in report["checks"]:  # type: ignore[index]
        check = raw  # type: ignore[assignment]
        marker = {"ok": "OK", "warn": "WARN", "error": "ERROR"}[check["status"]]
        print(f"[{marker}] {check['message']}")
        if check.get("detail"):
            print(f"       {check['detail']}")


def _doctor(args: argparse.Namespace) -> int:
    report = build_doctor_report(include_environment=not args.no_environment)
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
        help="Skip Node/npm/hardware probes and only check Python package profile consistency",
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
