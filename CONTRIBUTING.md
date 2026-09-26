# Contributing to AbstractFramework

Thank you for helping. This repository is the root of the AbstractFramework ecosystem: the
`abstractframework` meta-package (a pinned install profile with a few helpers), the one-line and
Mac installers, the workspace scripts, and the cross-package documentation. Each component
(AbstractCore, AbstractRuntime, AbstractGateway, the apps, …) lives in its own repository; open
issues and pull requests about a component there. The [README](README.md#package-map) links to
every component repository.

## What belongs here

- the meta-package: `pyproject.toml` pins, `abstractframework/` (`doctor`, `manifest`, release
  profile helpers) and `tests/`;
- the installers: `scripts/install.sh`, `scripts/install.ps1`, `scripts/uninstall.sh`, the two
  `.command` files and `scripts/lib/build_macos_installer.sh`;
- the workspace scripts (`scripts/clone.sh`, `deps.sh`, `build.sh`, `status.sh`, …);
- the cross-package docs in `docs/`, the architecture decision records in `docs/adr/` and the root
  backlog in `docs/backlog/`.

## Set up

To work on the meta-package alone:

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install pytest
python -m pip install -e . --no-deps
```

To work across the whole ecosystem from source, clone and build every sibling repository next to
this one (see [Workspace scripts](docs/workspace-scripts.md)):

```bash
./scripts/clone.sh
source ./scripts/build.sh
```

## Test

```bash
python -m pytest -q                      # meta-package, pins, manifest, installer behaviour
bash scripts/tests/test_inventory.sh     # package inventory and tiers
bash scripts/tests/test_repo_scripts.sh  # workspace scripts in a sandbox (no network)
python3 scripts/check_identity_sync.py   # every vendored identity copy matches (sibling checkouts)
sh scripts/install.sh --print            # the installer's plan, without changing anything
```

CI runs `python -m pytest -q`, builds the distribution, and runs the installers on Ubuntu, macOS
and Windows.

## Change the documentation

- Keep `README.md` and `docs/` consistent with each other and with the code; `docs/README.md`
  indexes every page.
- `docs/architecture.md` keeps its Mermaid diagrams in line with the released packages
  ([API](docs/api.md) lists the pins).
- After editing any page that `llms-full.txt` aggregates, regenerate it in the same change:

  ```bash
  python scripts/gen_llms_full.py           # regenerate
  python scripts/gen_llms_full.py --check   # fail when llms-full.txt is stale
  ```

  The generator follows the links of `docs/README.md` and refuses a top-level `docs/*.md` page
  the index does not link. `llms.txt` is edited by hand; keep its links in line with the docs.
- After a pin change, regenerate and check the install manifest:

  ```bash
  abstractframework manifest --write docs/installers/install-manifest.json
  abstractframework manifest --check docs/installers/install-manifest.json
  ```

  The release steps are in [release-and-manifest.md](docs/installers/release-and-manifest.md) and
  [ADR-0034](docs/adr/0034-framework-release-sequence-and-gates.md).

## Framework identity

`identity/abstractframework.json` is the one canonical description of the framework that every
About screen shows (name, website, author, licence, links, contact, and one entry per app). The
packages that render it carry byte-identical copies:

| Copy | Used by |
|---|---|
| `abstractcore/abstractcore/assets/abstractframework_identity.json` | `abstractcore.utils.identity` (the Assistant, the gateway's menu-bar icon and web console rows) |
| `abstractuic/ui-kit/src/abstractframework_identity.json` | the ui-kit About dialog (Code Web, Flow, Observer, Entity, Continuum, the gateway web console) |
| `abstractcode/tui/assets/abstractframework_identity.json` | the AbstractCode terminal client's `/about` |
| `abstractgateway/console-tui/assets/abstractframework_identity.json` | the gateway terminal console's About |

The rule: change the canonical file here first, copy it byte for byte into every consumer, then
run the check from a workspace where the sibling repositories sit next to this one:

```bash
python3 scripts/check_identity_sync.py
```

It compares bytes and fails on any drift or missing copy (`--lenient` reports a missing copy
without failing). It also checks the shared contract fixtures that several packages vendor: the
gateway version rows fixture (canonical in the ui-kit, copied into AbstractCore and the gateway
terminal console) and AbstractCore's console fixtures copied into the gateway terminal console.
Each copy ships with its own package release, so an identity change reaches users as those
packages are released.

## Pull requests

- Keep a pull request focused on one change and describe what a user sees differently.
- Add or update tests for behaviour changes; run the commands above before you push.
- Record user-visible changes in [CHANGELOG.md](CHANGELOG.md).
- For decisions that span packages, read the [ADR index](docs/adr/README.md) first; a new
  cross-package rule needs an ADR.

## Security and conduct

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md), not in a public
issue. Participation follows the [Code of Conduct](CODE_OF_CONDUCT.md).
