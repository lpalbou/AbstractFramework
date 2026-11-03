"""Internal dependency names belong to their registry, including opt-in crates."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _inventory(monkeypatch, root):
    path = Path(__file__).resolve().parents[1] / "scripts/lib/af_inventory.py"
    spec = importlib.util.spec_from_file_location("inventory_ecosystems", path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT_DIR", root)
    monkeypatch.setattr(module, "_origin", lambda _: "example/project")
    return module


def _package(inv, root, ident, kind, registry, name, deps=()):
    repo = root / ident
    (repo / ".git").mkdir(parents=True)
    if kind == "python":
        requirements = ",".join(f'"{name}>=0.1.0"' for name, _ in deps)
        (repo / "pyproject.toml").write_text(
            f'[project]\nname="{name}"\nversion="0.1.0"\ndependencies=[{requirements}]\n'
        )
    else:
        requirements = "\n".join(f'{name}="0.1.0"' for name, _ in deps)
        (repo / "Cargo.toml").write_text(
            f'[package]\nname="{name}"\nversion="0.1.0"\n[dependencies]\n{requirements}\n'
        )
    return inv.Package(ident, ident, "example/project", kind, ".", registry, name, 1 if deps else 0, list(deps))


def test_same_named_python_distribution_and_crate_resolve_independently(tmp_path, monkeypatch):
    inv = _inventory(monkeypatch, tmp_path)
    python = _package(inv, tmp_path, "pythonlib", "python", "pypi", "shared")
    rust = _package(inv, tmp_path, "rustlib", "rust", "crates", "shared")
    consumer = _package(inv, tmp_path, "consumer", "python", "pypi", "consumer", [("shared", "dep")])
    consumer.deps = [("pythonlib", "dep")]
    # Both registry orders must work; a flat name map silently selected the last one.
    assert inv.cmd_check([python, rust, consumer], None) == 0
    assert inv.cmd_check([rust, python, consumer], None) == 0


def test_optional_rust_capability_is_an_extra_edge(tmp_path, monkeypatch):
    inv = _inventory(monkeypatch, tmp_path)
    library = _package(inv, tmp_path, "generator", "rust", "crates", "generator")
    consumer = _package(inv, tmp_path, "player", "rust", "crates", "player", [("generator", "extra")])
    (consumer.dir / "Cargo.toml").write_text(
        '[package]\nname="player"\nversion="0.1.0"\n'
        '[dependencies]\ngenerator={version="0.1.0",optional=true}\n'
    )
    assert inv.cmd_check([library, consumer], None) == 0
    consumer.deps = [("generator", "dep")]
    assert inv.cmd_check([library, consumer], None) == 1
