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
KNOWN_COPIES = [
    SIBLINGS / "abstractcore" / "abstractcore" / "assets" / "abstractframework_identity.json",
    SIBLINGS / "abstractuic" / "ui-kit" / "src" / "abstractframework_identity.json",
    SIBLINGS / "abstractcode" / "tui" / "assets" / "abstractframework_identity.json",
    SIBLINGS / "abstractgateway" / "console-tui" / "assets" / "abstractframework_identity.json",
]


def main(argv: list[str]) -> int:
    strict = "--lenient" not in argv
    extra = [Path(a) for a in argv if a != "--lenient"]
    canonical = CANONICAL.read_bytes()
    failures = 0
    for path in KNOWN_COPIES + extra:
        if not path.exists():
            print(f"missing  {path}")
            failures += int(strict)
            continue
        copy = path.read_bytes()
        if copy == canonical:
            print(f"ok       {path}")
        else:
            print(f"DRIFT    {path} (copy identity/abstractframework.json over it)")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
