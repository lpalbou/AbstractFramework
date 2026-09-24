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
  python scripts/gen_llms_full.py
  ```

  `llms.txt` is edited by hand; keep its links in line with the docs.
- After a pin change, regenerate and check the install manifest:

  ```bash
  abstractframework manifest --write docs/installers/install-manifest.json
  abstractframework manifest --check docs/installers/install-manifest.json
  ```

  The release steps are in [release-and-manifest.md](docs/installers/release-and-manifest.md) and
  [ADR-0034](docs/adr/0034-framework-release-sequence-and-gates.md).

## Pull requests

- Keep a pull request focused on one change and describe what a user sees differently.
- Add or update tests for behaviour changes; run the commands above before you push.
- Record user-visible changes in [CHANGELOG.md](CHANGELOG.md).
- For decisions that span packages, read the [ADR index](docs/adr/README.md) first; a new
  cross-package rule needs an ADR.

## Security and conduct

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md), not in a public
issue. Participation follows the [Code of Conduct](CODE_OF_CONDUCT.md).
