# Release and Install Manifest

The install manifest is the machine-readable contract between a release and everything that
installs it: the bootstrap scripts, the docs, and any tool that wants the pinned versions. It is
generated from the root `abstractframework` release pins, never edited by hand:

```bash
abstractframework manifest                                   # print it
abstractframework manifest --write docs/installers/install-manifest.json
abstractframework manifest --check docs/installers/install-manifest.json
```

## Fields (schema version 2)

`install-manifest.json` is generated from `abstractframework/__init__.py` (`__version__`,
`RELEASE_VERSIONS`, `PACKAGE_DISTRIBUTIONS`, `NPM_RELEASE_VERSIONS`) and
`abstractframework/install_manifest.py`, and validated by `install-manifest.schema.json`.

| Field | Description |
|---|---|
| `schema_version` | `2` |
| `minimum_installer_version` | Oldest consumer that understands this manifest |
| `framework` | The `abstractframework` distribution, its version and `python_requires` |
| `source` | Repository URL and the Python symbol the pins come from |
| `profiles` | `light`, `apple`, `gpu`: pip requirement, platforms, prerequisites, whether local inference is installed |
| `python_packages` | Every pinned PyPI package: id, distribution name, version |
| `npm_apps` | Every npm app released with this version and its `npx` command |
| `bootstrap` | What the one-line scripts install: `gateway_version`, `python` (`3.12`), `tool_requirement`, `profile_extras`, `optional_extras`, `default_port`, script URLs and one-liners, the shared flag table (`sh`/`ps`/env names), the step list, and the uninstall commands |
| `post_install` | Console-first next steps: `entrypoint: "console"`, the `serve` command on `127.0.0.1`, `health_url`, `console_url`, the `claim` command and its token-file fallback, the `service` command, `doctor`, and the `npx` app commands |
| `security` | Whether secrets or signed native artifacts are present |

`scripts/install.sh` reads `bootstrap.gateway_version` from the manifest next to it and embeds the
same value for `curl | sh` use; `scripts/install.ps1` does the same. `python -m pytest -q` and
`bash scripts/tests/test_inventory.sh` fail when the scripts, the manifest and the root pins
disagree.

## Updating it for a release

1. Release the lower packages first, in the order of
   [ADR-0034](../adr/0034-framework-release-sequence-and-gates.md).
2. Change the pins in `pyproject.toml` and the matching dictionaries in
   `abstractframework/__init__.py`.
3. Regenerate the manifest: `abstractframework manifest --write docs/installers/install-manifest.json`
   (from the repository checkout, so it reads the edited source).
4. Update the embedded pins in `scripts/install.sh` (`AF_GATEWAY_PIN_DEFAULT`, `AF_NPM_APPS`,
   crates) and `scripts/install.ps1` (`$AfGatewayPinDefault`, `$AfNpmApps`, crates).
5. Run `python -m pytest -q` and `bash scripts/tests/test_inventory.sh`. CI's `bootstrap-smoke`
   job installs the published pin on Ubuntu, macOS and Windows.

## Signed artifacts

The bootstrap installs PyPI and npm packages and vendor installers, so the release pipeline
publishes no signed installers. Native apps that need signing (the AbstractAssistant `.app`)
publish their artifacts on their own release pages; see
[security-and-os-blocks.md](security-and-os-blocks.md#where-code-signing-still-applies).
