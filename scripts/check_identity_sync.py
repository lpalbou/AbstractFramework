#!/usr/bin/env python3
"""Check that every vendored copy of the framework identity matches the canonical file.

The canonical descriptor is ``identity/abstractframework.json`` in this repo. Each
application vendors a byte-identical copy (Python package data, a TypeScript
import, a Rust ``include_str!``) so that installed packages stay self-contained.
This script fails when a copy drifts, so a change to the canonical file is
followed by a copy into every consumer.

Usage: check_identity_sync.py [--lenient] [extra/copy.json ...]
  --lenient  a missing copy is reported but not fatal (default: a missing copy fails)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / "identity" / "abstractframework.json"
# Sibling repositories live side by side with this one.
SIBLINGS = ROOT.parent if (ROOT.parent / "abstractcore").is_dir() else ROOT
# Shared contract fixtures follow the same rule (canonical copy first, then the vendored copies).
FIXTURE_CANONICAL = SIBLINGS / "abstractuic" / "ui-kit" / "scripts" / "fixtures" / "gateway_version_rows.json"
FIXTURE_COPIES = [
    SIBLINGS / "abstractcore" / "tests" / "utils" / "fixtures" / "gateway_version_rows.json",
    SIBLINGS / "abstractgateway" / "console-tui" / "tests" / "fixtures" / "gateway_version_rows.json",
]
# The gateway console-tui vendors AbstractCore's console contract fixtures (canonical in abstractcore).
CONSOLE_FIXTURE_NAMES = ("engines_status.json", "host_profile.json", "job_completed.json", "job_running.json", "model_catalog.json", "models_installed.json")
CONSOLE_FIXTURE_CANONICAL_DIR = SIBLINGS / "abstractcore" / "console-tui" / "tests" / "fixtures"
CONSOLE_FIXTURE_COPY_DIR = SIBLINGS / "abstractgateway" / "console-tui" / "tests" / "fixtures"
KNOWN_COPIES = [
    SIBLINGS / "abstractcore" / "abstractcore" / "assets" / "abstractframework_identity.json",
    SIBLINGS / "abstractuic" / "ui-kit" / "src" / "abstractframework_identity.json",
    SIBLINGS / "abstractcode" / "tui" / "assets" / "abstractframework_identity.json",
    SIBLINGS / "abstractgateway" / "console-tui" / "assets" / "abstractframework_identity.json",
]


def main(argv: list[str]) -> int:
    strict = "--lenient" not in argv
    extra = [Path(a) for a in argv if a != "--lenient"]
    failures = 0
    groups = [(CANONICAL, KNOWN_COPIES + extra), (FIXTURE_CANONICAL, FIXTURE_COPIES)]
    groups += [(CONSOLE_FIXTURE_CANONICAL_DIR / name, [CONSOLE_FIXTURE_COPY_DIR / name]) for name in CONSOLE_FIXTURE_NAMES]
    for canonical_path, copies in groups:
        if not canonical_path.exists():
            print(f"missing  {canonical_path} (canonical)")
            failures += int(strict)
            continue
        failures += _check_copies(canonical_path.read_bytes(), canonical_path, copies, strict)
    return 1 if failures else 0


def _check_copies(canonical: bytes, canonical_path: Path, copies: list[Path], strict: bool) -> int:
    failures = 0
    for path in copies:
        if not path.exists():
            print(f"missing  {path}")
            failures += int(strict)
            continue
        copy = path.read_bytes()
        if copy == canonical:
            print(f"ok       {path}")
        else:
            print(f"DRIFT    {path} (copy {canonical_path} over it)")
            failures += 1
    return failures


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
