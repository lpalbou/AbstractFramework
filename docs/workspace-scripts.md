# Workspace scripts (working from source)

AbstractFramework is developed as one workspace: this repository at the root and every package
repository cloned next to its files (`abstractcore/`, `abstractgateway/`, `abstractuic/`, …). Each
directory is its own git repository. The scripts in `scripts/` let you clone, build, inspect,
commit, pull and push the whole set at once, always in dependency order.

If you only want to *use* the framework, install the published packages instead: see
[Install](install.md). This page is for contributors who build from the checkouts.

## The package inventory

`scripts/lib/packages.txt` is the single list every script reads. It has one row per published
package (29 packages in 21 repositories):

| Column | Meaning |
|---|---|
| `id` | Short package id used by the scripts (`abstractcore`, `panel-chat`, `code-cli`, …) |
| `repo` | Checkout directory under the workspace root (`.` is this repository) |
| `github` | GitHub `owner/Name`, used by `clone.sh` |
| `kind` | `python`, `npm`, `rust` or `meta` (the root meta-package) |
| `path` | Package directory inside the repository (`abstractuic/panel-chat`, `abstractcode/web`, `abstractgateway/console-tui`, …) |
| `registry`, `name` | Where it is published and under which name (PyPI distribution, npm package, crate) |
| `tier` | Dependency level: `0` has no internal dependency; otherwise one more than its highest dependency |
| `deps` | Internal dependency edges, `id:kind` |

Edge kinds explain *why* one package comes before another:

| Edge | Meaning |
|---|---|
| `dep` | Runtime dependency (pyproject `dependencies`, npm `dependencies`, Cargo `[dependencies]`) |
| `extra` | Only through an optional extra (for example `abstractcore[vision]` → `abstractvision`) |
| `peer` | npm peer dependency |
| `dev` | npm dev dependency bundled at build time from the registry |
| `alias` | Vite source alias to `../abstractuic/<package>/src`: the build needs the AbstractUIC checkout |
| `pin` | Exact `==` pin in the root `abstractframework` meta-package |
| `app` | Browser app version listed by the root install manifest |

`./scripts/deps.sh check` compares the inventory with the real `pyproject.toml`, `package.json`,
`Cargo.toml` and `vite.config.*` files and with each checkout's git origin, and fails on any
difference. Run it after you add a dependency between two packages, then update the row.

## Tiers: what comes first

`./scripts/deps.sh` prints every tier with its edges. The current order:

| Tier | Python (PyPI) | npm | Rust (crates.io) |
|---|---|---|---|
| 0 | abstractskill, abstractsemantics, AbstractMemory, abstractvision, abstractvoice, abstractmusic, abstractcamera | ui-kit, app-server, monitor-flow, monitor-gpu, monitor-memory, monitor-active-memory | abstracttui |
| 1 | abstract3d | panel-chat, flow | abstractgateway-console, abstractcode |
| 2 | abstractcore | observer, continuum, entity, code (web) | |
| 3 | AbstractRuntime | | |
| 4 | abstractagent, abstractassistant | | |
| 5 | abstractgateway | | |
| 6 | abstractframework (meta-package) | | |

Install, build and release tier by tier: a package is only built or published after everything it
depends on. To see what has to follow a change to one package, ask for its reverse dependencies:

```bash
./scripts/deps.sh rdeps abstractcore
```

The same inventory drives the release sequence described in
[ADR 0034](adr/0034-framework-release-sequence-and-gates.md).

## Commands

| Script | What it does |
|---|---|
| `./scripts/clone.sh [DIR]` | Clone every repository (tier order), or fast-forward the ones already cloned. `--list` prints the repositories. |
| `./scripts/deps.sh` | Tiers and dependency edges. Also `order`, `rdeps ID`, `check`, `versions`, `json`, `--kind python\|npm\|rust`. |
| `source ./scripts/build.sh` | Build every package from the checkouts, tier by tier, and stay in the virtualenv. See below. |
| `./scripts/status.sh` | Git overview of every repository, grouped by tier: branch, changes, unpushed and unpulled commits, and the packages each repository holds. `--short` shows only repositories with pending work. |
| `./scripts/status.sh --registry` | Adds local version vs latest published version on PyPI, npm and crates.io for every package (network). `--versions` shows local versions only; `--tiers` adds the dependency view. |
| `./scripts/pull.sh` | Fetch and fast-forward `main` everywhere. Never merges or rebases; a diverged repository is reported and left alone. `--dry-run` fetches and reports only. |
| `./scripts/commit.sh "message"` | Commit every dirty repository with the same message (`git add -A` per repository). Does not push. |
| `./scripts/push.sh` | Dry run: lists, per repository, the commits `main` would push. `--yes` pushes them. Never force-pushes, never pushes tags, skips a diverged `main`. `--fetch` refreshes the upstream first. |
| `./scripts/install.sh` | Install the *published* release (not the checkouts); see [Install](install.md). `--print` shows the plan. |

`pull.sh` and `push.sh` accept `--only repo1,repo2` to work on a subset.

A typical day:

```bash
./scripts/pull.sh --dry-run      # what changed upstream
./scripts/pull.sh                # fast-forward
source ./scripts/build.sh        # rebuild what you work on
./scripts/status.sh --short      # what you changed
./scripts/commit.sh "Describe the change"
./scripts/push.sh                # review, then:
./scripts/push.sh --yes
```

## Building from source

`build.sh` builds the three ecosystems in dependency order:

- **Python**: editable installs (`pip install -e`) of the 13 Python packages and the root
  meta-package into one virtualenv. Third-party dependencies still come from PyPI.
- **npm**: the seven AbstractUIC packages (installed once at the `abstractuic` workspace root, built
  per package), then the apps `flow`, `observer`, `continuum`, `entity` and `code` (web).
- **Rust**: `cargo build` of `abstracttui`, `abstractcode` (`abstractcode/tui`) and
  `abstractgateway-console` (`abstractgateway/console-tui`).

| Option | Effect |
|---|---|
| `--python`, `--npm`, `--rust` | Build only the selected ecosystems (they combine). Default: all three. |
| `--light` (default), `--apple`, `--gpu` | Python dependency profile; also `AF_BUILD_PROFILE=light\|apple\|gpu\|auto`. |
| `--clean` | Delete the virtualenv first. |
| `--plan` | Print the tier-ordered build plan and build nothing. |
| `AF_VENV_DIR=path` | Virtualenv location (default `<root>/.venv`). The `-local` launchers use the same variable. |

The npm and cargo output is kept in a log per package; the terminal shows one line per package and
the log tail when a step fails. The script exits non-zero when any selected ecosystem failed.

Prerequisites: Python 3.10+, Node.js 18+ for the npm packages, a Rust toolchain for the crates.

## Running the stack

| Published packages | Local checkouts | Starts |
|---|---|---|
| `start.sh` / `af.sh` | `start-local.sh` / `af-local.sh` | The whole stack under one supervisor: gateway first, then the apps |
| `gateway.sh` | `gateway-local.sh` | AbstractGateway (control plane, port 8080) |
| `flow.sh` | `flow-local.sh` | `@abstractframework/flow` |
| `observer.sh` | `observer-local.sh` | `@abstractframework/observer` |
| `code.sh` | `code-local.sh` | `@abstractframework/code` (web) |
| `console.sh` | `console-local.sh` | `@abstractframework/continuum` |
| `entity.sh` | `entity-local.sh` | `@abstractframework/entity` |
| `assistant.sh` | `assistant-local.sh` | AbstractAssistant (tray app) |

The stack launchers use one port map: gateway 8080, observer 3001, continuum 3002, code 3003,
entity 3004, flow 3005 (each overridable with `ABSTRACT<APP>_PORT`). `start-local.sh --build`
runs `build.sh` first.

## Script tests

```bash
bash scripts/tests/test_inventory.sh      # inventory vs package files, install pins vs manifest
bash scripts/tests/test_repo_scripts.sh   # clone/status/commit/push/pull/build in an offline sandbox
bash scripts/tests/test_af_supervisor.sh  # stack supervisor semantics with stub services
```

All three run against temporary directories and stub services; they do not modify the workspace.
