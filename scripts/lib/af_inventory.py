#!/usr/bin/env python3
"""AbstractFramework package inventory helper.

Reads scripts/lib/packages.txt (the single source of truth shared with the
bash loader scripts/lib/repo_groups.sh) and answers the questions the
workspace scripts need:

  tiers     what must be installed/released first, per tier, with the edges
            (the "why") -- the default view of scripts/deps.sh
  order     flat dependency order, one package per line (machine friendly)
  rdeps ID  every package that depends on ID, directly or transitively
            ("if I bump ID, what has to follow it")
  versions  local version per package; with --registry also the latest
            version on PyPI / npm / crates.io (network)
  check     validate the manifest against the real package files: tiers,
            edge targets, pyproject / package.json / Cargo.toml / Vite
            aliases, root pins, checkout presence and git origins
  json      the inventory as JSON

Standard library only. Python 3.9+ (the `check` command needs tomllib, i.e.
Python 3.11+, or the `tomli` backport).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
ROOT_DIR = Path(os.environ.get("AF_ROOT_DIR") or LIB_DIR.parent.parent).resolve()
MANIFEST = Path(os.environ.get("AF_PACKAGES_FILE") or LIB_DIR / "packages.txt")

KINDS = ("python", "npm", "rust", "meta")
EDGE_KINDS = {
    "dep": "runtime dependency",
    "extra": "optional extra",
    "peer": "npm peer dependency",
    "dev": "bundled at build time (npm registry)",
    "alias": "Vite source alias to the ../abstractuic checkout",
    "pin": "root exact pin",
    "app": "root install manifest app",
}
REGISTRY_LABEL = {"pypi": "PyPI", "npm": "npm", "crates": "crates.io"}

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------
@dataclass
class Package:
    id: str
    repo: str
    github: str
    kind: str
    path: str
    registry: str
    name: str
    tier: int
    deps: list[tuple[str, str]] = field(default_factory=list)
    line: int = 0

    @property
    def dir(self) -> Path:
        base = ROOT_DIR if self.repo == "." else ROOT_DIR / self.repo
        return base if self.path == "." else base / self.path

    @property
    def repo_dir(self) -> Path:
        return ROOT_DIR if self.repo == "." else ROOT_DIR / self.repo

    @property
    def repo_label(self) -> str:
        return "abstractframework (root)" if self.repo == "." else self.repo

    @property
    def location(self) -> str:
        repo = "." if self.repo == "." else self.repo
        return repo if self.path == "." else f"{repo}/{self.path}"


class ManifestError(Exception):
    pass


def load_manifest(path: Path = MANIFEST) -> list[Package]:
    packages: list[Package] = []
    seen: set[str] = set()
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        cols = [col.strip() for col in line.split("|")]
        if len(cols) != 9:
            raise ManifestError(f"{path}:{lineno}: expected 9 columns, got {len(cols)}")
        pid, repo, github, kind, ppath, registry, name, tier, deps = cols
        if pid in seen:
            raise ManifestError(f"{path}:{lineno}: duplicate id {pid!r}")
        if kind not in KINDS:
            raise ManifestError(f"{path}:{lineno}: unknown kind {kind!r}")
        if registry not in REGISTRY_LABEL:
            raise ManifestError(f"{path}:{lineno}: unknown registry {registry!r}")
        if not tier.isdigit():
            raise ManifestError(f"{path}:{lineno}: tier must be an integer, got {tier!r}")
        edges: list[tuple[str, str]] = []
        if deps != "-":
            for item in deps.split(","):
                dep_id, _, edge_kind = item.strip().partition(":")
                if edge_kind not in EDGE_KINDS:
                    raise ManifestError(f"{path}:{lineno}: edge {item!r} has unknown kind {edge_kind!r}")
                edges.append((dep_id, edge_kind))
        seen.add(pid)
        packages.append(Package(pid, repo, github, kind, ppath, registry, name, int(tier), edges, lineno))
    ids = {p.id for p in packages}
    for p in packages:
        for dep_id, _ in p.deps:
            if dep_id not in ids:
                raise ManifestError(f"{path}:{p.line}: {p.id} depends on unknown id {dep_id!r}")
    return packages


def computed_tiers(packages: list[Package]) -> dict[str, int]:
    by_id = {p.id: p for p in packages}
    memo: dict[str, int] = {}
    stack: list[str] = []

    def tier(pid: str) -> int:
        if pid in memo:
            return memo[pid]
        if pid in stack:
            raise ManifestError("dependency cycle: " + " -> ".join(stack + [pid]))
        stack.append(pid)
        deps = by_id[pid].deps
        value = 0 if not deps else 1 + max(tier(d) for d, _ in deps)
        stack.pop()
        memo[pid] = value
        return value

    for p in packages:
        tier(p.id)
    return memo


def tier_mismatches(packages: list[Package]) -> list[str]:
    real = computed_tiers(packages)
    return [
        f"{p.id}: manifest says tier {p.tier}, its edges make it tier {real[p.id]}"
        for p in packages
        if p.tier != real[p.id]
    ]


def ordered(packages: list[Package], kind: str | None = None) -> list[Package]:
    selected = [p for p in packages if kind in (None, p.kind)]
    return sorted(selected, key=lambda p: (p.tier, KINDS.index(p.kind), p.line))


# --------------------------------------------------------------------------
# Local versions
# --------------------------------------------------------------------------
def _section_value(text: str, section: str, key: str) -> str | None:
    """Value of `key = "..."` inside `[section]` of a TOML file (no tomllib needed)."""
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_section = stripped == f"[{section}]"
            continue
        if in_section:
            m = re.match(rf'{re.escape(key)}\s*=\s*["\']([^"\']+)["\']', stripped)
            if m:
                return m.group(1)
    return None


def _python_dynamic_version(pkg_dir: Path, text: str) -> str | None:
    m = re.search(r'version\s*=\s*\{\s*attr\s*=\s*["\']([\w.]+)["\']', text)
    if m:
        module = m.group(1).rsplit(".", 1)[0].split(".")
        for base in (pkg_dir / "src", pkg_dir):
            for candidate in (base.joinpath(*module).with_suffix(".py"), base.joinpath(*module, "__init__.py")):
                if candidate.is_file():
                    vm = re.search(r'^__version__\s*(?::\s*str\s*)?=\s*["\']([^"\']+)["\']',
                                   candidate.read_text(encoding="utf-8"), re.M)
                    if vm:
                        return vm.group(1)
    m = re.search(r'\[tool\.hatch\.version\][^\[]*?path\s*=\s*["\']([^"\']+)["\']', text, re.S)
    if m and (pkg_dir / m.group(1)).is_file():
        vm = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', (pkg_dir / m.group(1)).read_text(encoding="utf-8"), re.M)
        if vm:
            return vm.group(1)
    return None


def local_version(p: Package) -> str | None:
    """Version declared by the checkout, or None when it is not cloned/readable."""
    try:
        if p.kind in ("python", "meta"):
            text = (p.dir / "pyproject.toml").read_text(encoding="utf-8")
            return _section_value(text, "project", "version") or _python_dynamic_version(p.dir, text)
        if p.kind == "npm":
            return json.loads((p.dir / "package.json").read_text(encoding="utf-8")).get("version")
        if p.kind == "rust":
            return _section_value((p.dir / "Cargo.toml").read_text(encoding="utf-8"), "package", "version")
    except FileNotFoundError:
        return None
    return None


# --------------------------------------------------------------------------
# Registries (network)
# --------------------------------------------------------------------------
USER_AGENT = "abstractframework-scripts/1 (https://github.com/lpalbou/AbstractFramework)"


def _get_json(url: str, timeout: float) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https hosts)
        return json.loads(resp.read().decode("utf-8"))


def registry_version(p: Package, timeout: float = 15.0) -> tuple[str | None, str | None]:
    """(latest version, error). A 404 means 'never published' (version None, no error)."""
    try:
        if p.registry == "pypi":
            data = _get_json(f"https://pypi.org/pypi/{urllib.parse.quote(p.name)}/json", timeout)
            return data["info"]["version"], None
        if p.registry == "npm":
            name = urllib.parse.quote(p.name, safe="@")
            data = _get_json(f"https://registry.npmjs.org/{name.replace('/', '%2F')}", timeout)
            return data.get("dist-tags", {}).get("latest"), None
        if p.registry == "crates":
            data = _get_json(f"https://crates.io/api/v1/crates/{urllib.parse.quote(p.name)}", timeout)
            crate = data["crate"]
            return crate.get("max_stable_version") or crate.get("max_version"), None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, None
        return None, f"HTTP {exc.code}"
    except Exception as exc:  # network down, DNS, timeout, bad JSON
        return None, f"{type(exc).__name__}: {exc}"
    return None, f"unknown registry {p.registry}"


def _vkey(v: str) -> tuple:
    parts = re.split(r"[.+-]", v)
    return tuple((0, int(x)) if x.isdigit() else (1, x) for x in parts)


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------
def tier_title(t: int, max_tier: int) -> str:
    if t == 0:
        return f"Tier {t} — no internal dependencies: install / release these first"
    return f"Tier {t} — needs tier 0 first" if t == 1 else f"Tier {t} — needs tiers 0-{t - 1} first"


def cmd_tiers(packages: list[Package], args) -> int:
    by_id = {p.id: p for p in packages}
    rows = ordered(packages, args.kind)
    max_tier = max((p.tier for p in packages), default=0)
    current = None
    for p in rows:
        if p.tier != current:
            current = p.tier
            print()
            print(c("1", tier_title(p.tier, max_tier)))
            print("  " + "─" * 74)
        name = p.name
        if args.versions:
            name += f" {local_version(p) or '(not cloned)'}"
        print(f"  {c('33', f'{p.kind:<6}')} {c('1', f'{p.id:<22}')} {name:<48} {c('2', p.location)}")
        groups: dict[str, list[str]] = {}
        for dep_id, kind in p.deps:
            groups.setdefault(kind, []).append(f"{dep_id} (t{by_id[dep_id].tier})")
        for kind, items in groups.items():
            print(f"  {'':<6} {'':<22} {c('36', f'<- {kind:<5}')} {', '.join(items)}")
    print()
    print(c("2", "Edge kinds: " + "; ".join(f"{k} = {v}" for k, v in EDGE_KINDS.items())))
    problems = tier_mismatches(packages)
    for msg in problems:
        print(c("31", f"ERROR: {msg}"), file=sys.stderr)
    return 1 if problems else 0


def cmd_order(packages: list[Package], args) -> int:
    for p in ordered(packages, args.kind):
        print(f"{p.tier}\t{p.kind}\t{p.id}\t{p.name}\t{p.location}")
    return 1 if tier_mismatches(packages) else 0


def cmd_rdeps(packages: list[Package], args) -> int:
    by_id = {p.id: p for p in packages}
    if args.id not in by_id:
        print(f"ERROR: unknown package id {args.id!r}; ids: {', '.join(sorted(by_id))}", file=sys.stderr)
        return 2
    users: dict[str, list[tuple[str, str]]] = {}
    for p in packages:
        for dep_id, kind in p.deps:
            users.setdefault(dep_id, []).append((p.id, kind))
    seen: dict[str, str] = {}
    frontier = [args.id]
    while frontier:
        nxt = []
        for pid in frontier:
            for user, kind in users.get(pid, []):
                if user not in seen:
                    seen[user] = f"{kind} on {pid}"
                    nxt.append(user)
        frontier = nxt
    print(f"Packages that depend on {args.id} ({by_id[args.id].name}), in the order to follow it:")
    if not seen:
        print("  (none)")
    for p in ordered([by_id[u] for u in seen]):
        print(f"  tier {p.tier}  {p.kind:<6} {p.id:<22} via {seen[p.id]}")
    return 0


def cmd_versions(packages: list[Package], args) -> int:
    rows = ordered(packages, args.kind)
    remote: dict[str, tuple[str | None, str | None]] = {}
    if args.registry:
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            futures = {pool.submit(registry_version, p, args.timeout): p.id for p in rows}
            for fut in concurrent.futures.as_completed(futures):
                remote[futures[fut]] = fut.result()
    header = f"  {'tier':<4} {'kind':<6} {'package':<22} {'registry name':<42} {'local':<10}"
    if args.registry:
        header += f" {'registry':<10} status"
    print(c("1", header))
    errors = 0
    counts: dict[str, int] = {}
    for p in rows:
        local = local_version(p)
        line = f"  {p.tier:<4} {p.kind:<6} {p.id:<22} {p.name:<42} {(local or 'missing'):<10}"
        if args.registry:
            latest, err = remote[p.id]
            if err:
                status, color = f"lookup failed ({err})", "31"
                errors += 1
            elif latest is None:
                status, color = f"not on {REGISTRY_LABEL[p.registry]}", "33"
            elif local is None:
                status, color = "not cloned", "2"
            elif local == latest:
                status, color = "= published", "32"
            elif _vkey(local) > _vkey(latest):
                status, color = "local ahead (unreleased)", "33"
            else:
                status, color = "registry ahead (pull?)", "31"
            counts[status.split(" (")[0]] = counts.get(status.split(" (")[0], 0) + 1
            line += f" {(latest or '-'):<10} {c(color, status)}"
        print(line)
    if args.registry:
        print()
        print("  " + " · ".join(f"{k}: {n}" for k, n in sorted(counts.items())))
    return 1 if errors else 0


def _load_toml(path: Path) -> dict:
    try:
        import tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # Python < 3.11
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ModuleNotFoundError as exc:
            raise SystemExit("ERROR: `check` needs Python 3.11+ (tomllib) or `pip install tomli`") from exc
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _req_name(req: str) -> str:
    return re.match(r"\s*([A-Za-z0-9_.-]+)", req).group(1).lower().replace("_", "-")


def declared_edges(p: Package, by_name: dict[str, Package]) -> set[tuple[str, str]] | None:
    """Internal edges as declared by the package's own files (None = unreadable)."""
    edges: set[tuple[str, str]] = set()
    if p.kind in ("python", "meta"):
        pyproject = p.dir / "pyproject.toml"
        if not pyproject.is_file():
            return None
        project = _load_toml(pyproject)["project"]
        hard = {_req_name(r) for r in project.get("dependencies", [])}
        optional = {_req_name(r) for reqs in project.get("optional-dependencies", {}).values() for r in reqs}
        own = p.name.lower()
        hard_kind = "pin" if p.kind == "meta" else "dep"
        for name in hard:
            if name in by_name and name != own:
                edges.add((by_name[name].id, hard_kind))
        for name in optional - hard:
            if name in by_name and name != own:
                edges.add((by_name[name].id, "extra"))
        if p.kind == "meta":
            init = (p.dir / "abstractframework" / "__init__.py").read_text(encoding="utf-8")
            block = re.search(r"NPM_RELEASE_VERSIONS[^=]*=\s*\{(.*?)\}", init, re.S)
            for npm_name in re.findall(r'"(@abstractframework/[^"]+)"', block.group(1) if block else ""):
                if npm_name.lower() in by_name:
                    edges.add((by_name[npm_name.lower()].id, "app"))
        return edges
    if p.kind == "npm":
        pkg_json = p.dir / "package.json"
        if not pkg_json.is_file():
            return None
        data = json.loads(pkg_json.read_text(encoding="utf-8"))
        found: dict[str, str] = {}
        for section, kind in (("devDependencies", "dev"), ("peerDependencies", "peer"), ("dependencies", "dep")):
            for name in data.get(section) or {}:
                if name.lower() in by_name:
                    found[by_name[name.lower()].id] = kind  # later sections win: dep > peer > dev
        # Source aliases into the sibling AbstractUIC checkout.
        uic = {q.path: q.id for q in by_name.values() if q.repo == "abstractuic"}
        for cfg in sorted(p.dir.glob("vite.config.*")):
            for sub in re.findall(r"abstractuic/([a-z0-9-]+)/src", cfg.read_text(encoding="utf-8")):
                if sub in uic and uic[sub] not in found:
                    found[uic[sub]] = "alias"
        edges.update((pid, kind) for pid, kind in found.items() if pid != p.id)
        return edges
    if p.kind == "rust":
        cargo = p.dir / "Cargo.toml"
        if not cargo.is_file():
            return None
        data = _load_toml(cargo)
        for name in data.get("dependencies", {}):
            if name.lower() in by_name and by_name[name.lower()].kind == "rust" and name.lower() != p.name.lower():
                edges.add((by_name[name.lower()].id, "dep"))
        return edges
    return None


def _origin(repo_dir: Path) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(repo_dir), "remote", "get-url", "origin"],
                             capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", out)
    return m.group(1) if m else out


def cmd_check(packages: list[Package], args) -> int:
    problems: list[str] = []
    notes: list[str] = []
    by_name = {p.name.lower(): p for p in packages}
    problems += tier_mismatches(packages)
    repos: dict[str, Package] = {}
    for p in packages:
        repos.setdefault(p.repo, p)
        if repos[p.repo].github != p.github:
            problems.append(f"{p.id}: github {p.github} disagrees with {repos[p.repo].id} ({repos[p.repo].github}) in the same repo")
    for repo, p in repos.items():
        if not (p.repo_dir / ".git").exists():
            notes.append(f"{p.repo_label}: not cloned (run scripts/clone.sh) — its packages are not checked")
            continue
        origin = _origin(p.repo_dir)
        if origin is None:
            problems.append(f"{p.repo_label}: no `origin` remote")
        elif origin.lower() != p.github.lower():
            problems.append(f"{p.repo_label}: origin is {origin}, manifest says {p.github}")
    for p in packages:
        if not (p.repo_dir / ".git").exists():
            continue
        declared = declared_edges(p, by_name)
        if declared is None:
            problems.append(f"{p.id}: no package file at {p.location}")
            continue
        version = local_version(p)
        if version is None:
            problems.append(f"{p.id}: cannot read the local version at {p.location}")
        manifest_edges = set(p.deps)
        for edge in sorted(declared - manifest_edges):
            problems.append(f"{p.id}: {p.location} declares {edge[0]}:{edge[1]}, missing from packages.txt")
        for edge in sorted(manifest_edges - declared):
            problems.append(f"{p.id}: packages.txt lists {edge[0]}:{edge[1]}, not declared by {p.location}")
        if p.kind in ("python", "meta"):
            declared_name = _load_toml(p.dir / "pyproject.toml")["project"]["name"]
            if declared_name != p.name:
                problems.append(f"{p.id}: pyproject name is {declared_name!r}, packages.txt says {p.name!r}")
        elif p.kind == "npm":
            declared_name = json.loads((p.dir / "package.json").read_text(encoding="utf-8")).get("name")
            if declared_name != p.name:
                problems.append(f"{p.id}: package.json name is {declared_name!r}, packages.txt says {p.name!r}")
        elif p.kind == "rust":
            declared_name = _load_toml(p.dir / "Cargo.toml")["package"]["name"]
            if declared_name != p.name:
                problems.append(f"{p.id}: Cargo.toml name is {declared_name!r}, packages.txt says {p.name!r}")
    for n in notes:
        print(c("2", f"note: {n}"))
    for msg in problems:
        print(c("31", f"FAIL: {msg}"))
    if problems:
        print(c("31", f"packages.txt check: {len(problems)} problem(s)"))
        return 1
    print(c("32", f"packages.txt check: OK ({len(packages)} packages in {len(repos)} repositories; "
                  "tiers, edges, names and origins match the checkouts)"))
    return 0


def cmd_json(packages: list[Package], args) -> int:
    out = []
    for p in ordered(packages):
        out.append({
            "id": p.id, "repo": p.repo, "github": p.github, "kind": p.kind, "path": p.path,
            "registry": p.registry, "name": p.name, "tier": p.tier,
            "deps": [{"id": d, "kind": k} for d, k in p.deps],
            "local_version": local_version(p),
        })
    json.dump(out, sys.stdout, indent=2)
    print()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="af_inventory.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd")
    for name in ("tiers", "order", "versions"):
        sp = sub.add_parser(name)
        sp.add_argument("--kind", choices=KINDS)
        if name == "tiers":
            sp.add_argument("--versions", action="store_true", help="show the local version of each package")
        if name == "versions":
            sp.add_argument("--registry", action="store_true", help="also query PyPI / npm / crates.io")
            sp.add_argument("--timeout", type=float, default=15.0)
    sp = sub.add_parser("rdeps")
    sp.add_argument("id")
    sub.add_parser("check")
    sub.add_parser("json")
    args = parser.parse_args(argv)
    if args.cmd is None:
        args = parser.parse_args(["tiers"] + (argv or []))
    try:
        packages = load_manifest()
    except (ManifestError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    handler = {
        "tiers": cmd_tiers, "order": cmd_order, "rdeps": cmd_rdeps,
        "versions": cmd_versions, "check": cmd_check, "json": cmd_json,
    }[args.cmd]
    return handler(packages, args)


if __name__ == "__main__":
    sys.exit(main())
