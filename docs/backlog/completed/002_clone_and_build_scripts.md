# 002 — Fix clone.sh & Create build.sh for Local Development

## Summary

Rewrite `scripts/clone.sh` so AbstractFramework IS the root directory and sibling
repos are cloned directly into it (no redundant `AbstractFramework-repos/` nesting).
Create `scripts/build.sh` that installs every Python package in editable mode
(dependency order) and builds every npm package — all from local checkouts only —
inside a dedicated `.venv`.

## Why

- **clone.sh** currently clones a duplicate of AbstractFramework into the target
  directory alongside all other repos, which is confusing and wasteful.
- There is no single command to build the entire framework from local source for
  development. Developers must manually `pip install -e` each package in the right
  order and separately build npm packages.

## Scope

### In scope

| Item | Detail |
|------|--------|
| Rewrite `scripts/clone.sh` | AbstractFramework = root; clone only siblings into it |
| Update `.gitignore` | Ignore cloned sibling repo directories at root level |
| Create `scripts/build.sh` | Editable-install all 12 Python packages in correct dependency order into `.venv`; build all 4 npm targets |
| Dependency order | Tier 0 → Tier 4 (see below) |

### Out of scope

- Publishing to PyPI / npm (this is dev-only)
- CI/CD pipeline (future task)
- Remote/cloud install scripts

## Dependencies

- Python 3.10+ with `venv` module
- Node.js 18+ with npm (optional; only for UI packages)
- git

## Python Install Order (editable mode)

```
Tier 0  abstractsemantics    (PyYAML only)
        abstractmemory       (no required deps)
        abstractvision       (external only: torch, diffusers…)
        abstractvoice        (external only: piper-tts, faster-whisper…)
Tier 1  abstractcore         (pydantic, httpx; optional abstractvision)
        abstractruntime      (→ abstractsemantics)
Tier 2  abstractagent        (→ abstractcore, abstractruntime)
        abstractgateway      (→ abstractruntime)
Tier 3  abstractflow         (→ abstractruntime, abstractcore)
        abstractcode         (→ abstractagent, abstractruntime, abstractcore)
        abstractassistant    (→ abstractagent, abstractvoice, abstractcore)
Tier 4  abstractframework    (meta-package → all above)
```

## npm Build Targets

1. `abstractuic/` — monorepo (workspaces: ui-kit → panel-chat, monitor-*)
2. `abstractobserver/` — standalone Vite/React app
3. `abstractcode/web/` — browser coding assistant
4. `abstractflow/web/frontend/` — visual workflow editor

## Expected Outcomes

- `./scripts/clone.sh` produces a flat structure with AbstractFramework as root
- `./scripts/build.sh` creates `.venv`, installs everything, builds npm packages
- Developer can `source .venv/bin/activate` and immediately use all packages
- No packages fetched from PyPI/npm for AbstractFramework packages (only for
  third-party dependencies like pydantic, react, etc.)

---

## Report

### Completed

| Deliverable | File | Notes |
|---|---|---|
| Rewritten `clone.sh` | `scripts/clone.sh` | AbstractFramework = root; 13 siblings cloned into it; two usage modes (in-repo / fresh target) |
| New `build.sh` | `scripts/build.sh` | `.venv` creation, 12 Python packages in 5-tier editable install, 4 npm build targets, `--python` / `--npm` flags |
| Updated `.gitignore` | `.gitignore` | All 13 sibling repo dirs + `node_modules/` + `package-lock.json` |

### Design decisions

- **Editable installs (`pip install -e`)**: chosen for development so code changes
  are reflected immediately without reinstalling.
- **`--no-deps` on the meta-package (Tier 4)**: all internal deps are already
  installed from local source; avoids pip trying to fetch pinned versions from PyPI.
- **`hatchling` pre-installed**: three packages (abstractruntime, abstractgateway,
  abstractmemory) use hatchling as their build backend; pre-installing avoids
  repeated downloads during editable installs.
- **npm `--no-audit --no-fund`**: keeps CI output clean; security auditing is
  handled elsewhere.
- **Graceful npm fallback**: if Node.js is not installed, npm builds are skipped
  with a WARNING (not a hard failure), since only UI packages need it.
