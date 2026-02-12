"""
Pytest bootstrap for AbstractMusic.

This repository uses a `src/` layout for the `abstractmusic` package. In local
repo test runs (without an editable install), we add `src/` to `sys.path` so
tests can import `abstractmusic` directly.
"""

from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    if src.exists() and src.is_dir():
        sys.path.insert(0, str(src))

