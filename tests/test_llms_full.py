"""llms-full.txt carries the user docs the docs index links, and stays fresh."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _gen():
    spec = importlib.util.spec_from_file_location("gen_llms_full", ROOT / "scripts" / "gen_llms_full.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_top_level_docs_page_is_included() -> None:
    pages = set(_gen().docs_pages(ROOT))
    top = {f"docs/{p.name}" for p in (ROOT / "docs").glob("*.md")}
    assert "docs/troubleshooting.md" in top
    assert top - pages == set()


def test_no_planning_or_research_pages_are_included() -> None:
    gen = _gen()
    for rel in gen.docs_pages(ROOT):
        assert rel.split("/")[1] not in gen.NON_USER_DIRS, rel
    text = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
    for folder in gen.NON_USER_DIRS:
        assert f"\n--- docs/{folder}/" not in text, folder


def test_a_page_missing_from_the_index_fails(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("[A](a.md)\n", encoding="utf-8")
    (tmp_path / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "docs" / "b.md").write_text("# B\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="docs/b.md"):
        _gen().docs_pages(tmp_path)


def test_llms_full_is_current() -> None:
    current = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
    assert current == _gen().render(ROOT), "llms-full.txt is stale; run python scripts/gen_llms_full.py"
