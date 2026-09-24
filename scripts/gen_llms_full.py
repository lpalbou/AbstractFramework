#!/usr/bin/env python3
from __future__ import annotations

import argparse
import posixpath
import re
from pathlib import Path


# Repository files that come first, before the user docs.
PREAMBLE: list[str] = [
    "README.md",
    "llms.txt",
    "pyproject.toml",
    "abstractframework/__init__.py",
    "abstractframework/install_manifest.py",
    "abstractframework/cli.py",
]

INDEX = "docs/README.md"
# Folders under docs/ that are not user documentation (decisions, planning,
# engineering notes, research); their pages never enter llms-full.txt.
NON_USER_DIRS = ("adr", "backlog", "claude", "prompts", "reports", "research", "skills")

_LINK = re.compile(r"\]\(([^\s)#]+)(?:#[^\s)]*)?\)")


def _is_user_page(rel: str) -> bool:
    parts = rel.split("/")
    return parts[0] == "docs" and not (len(parts) > 2 and parts[1] in NON_USER_DIRS)


def docs_pages(repo_root: Path) -> list[str]:
    """The user pages, in the order `docs/README.md` links them.

    The index is followed from `docs/README.md`: a linked page is included; a
    linked folder, or a folder's `README.md`, is a sub-index whose own links
    are followed the same way. Every top-level `docs/*.md` page must be
    reachable, so a new page cannot be left out silently.
    """

    pages: list[str] = []

    def visit(rel: str) -> None:
        if rel in pages:
            return
        pages.append(rel)
        if not rel.endswith("/README.md"):
            return
        base = posixpath.dirname(rel)
        for dest in _LINK.findall((repo_root / rel).read_text(encoding="utf-8")):
            if re.match(r"[A-Za-z][\w+.-]*:", dest) or dest.startswith("/"):
                continue
            target = posixpath.normpath(posixpath.join(base, dest))
            if (repo_root / target).is_dir():
                target = posixpath.join(target, "README.md")
            if not target.endswith(".md") or not _is_user_page(target):
                continue
            if not (repo_root / target).is_file():
                raise SystemExit(f"{rel} links to a missing page: {dest}")
            visit(target)

    visit(INDEX)
    unlisted = sorted(
        f"docs/{p.name}" for p in (repo_root / "docs").glob("*.md") if f"docs/{p.name}" not in pages
    )
    if unlisted:
        raise SystemExit(f"{INDEX} does not link these pages: {', '.join(unlisted)}")
    return pages


def render(repo_root: Path) -> str:
    parts: list[str] = []
    parts.append("# AbstractFramework - llms-full\n")
    parts.append("> Full text of key files from this repo. Sections are separated by `--- <path> ---`.\n")

    for rel in PREAMBLE + docs_pages(repo_root):
        p = repo_root / rel
        if not p.exists():
            raise SystemExit(f"Missing file: {rel}")
        parts.append(f"\n--- {rel} ---\n")
        parts.append(p.read_text(encoding="utf-8"))
        if not parts[-1].endswith("\n"):
            parts.append("\n")
    return "".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate llms-full.txt from the docs index.")
    parser.add_argument("--check", action="store_true", help="fail when llms-full.txt is stale")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    out = repo_root / "llms-full.txt"
    expected = render(repo_root)
    if args.check:
        if out.read_text(encoding="utf-8") != expected:
            raise SystemExit("llms-full.txt is stale; run python scripts/gen_llms_full.py")
        print("llms-full.txt is current")
        return
    out.write_text(expected, encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
