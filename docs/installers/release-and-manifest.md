# Release Pipeline and Manifest

This guide describes how installer artifacts are built, signed, and published, plus
the manifest format the Installer Manager uses to discover components. The current
profile manifest is generated from the root `abstractframework` release pins:

```bash
abstractframework manifest --check docs/installers/install-manifest.json
```

## Generated profile manifest (schema version 1)

`install-manifest.json` is what installers can consume today. It is generated from
`abstractframework/__init__.py` (`__version__`, `RELEASE_VERSIONS`, `PACKAGE_DISTRIBUTIONS`,
`NPM_RELEASE_VERSIONS`) and `abstractframework/install_manifest.py`, and validated by
`install-manifest.schema.json`.

| Field | Description |
|---|---|
| `schema_version` | Manifest schema version (`1`) |
| `minimum_installer_version` | Oldest installer that understands this manifest |
| `framework` | The `abstractframework` distribution, its version and `python_requires` |
| `source` | Repository URL and the Python symbol the pins come from |
| `profiles` | `light`, `apple`, `gpu`: pip requirement, platforms, prerequisites, whether local inference is installed |
| `python_packages` | Every pinned PyPI package: id, distribution name, version |
| `npm_apps` | Every npm app released with this version and its `npx` command |
| `post_install` | Commands to run after install (`abstractframework doctor`, `abstractcore --config`, gateway + flow) |
| `security` | Whether secrets or signed native artifacts are present |

For abstractframework 0.1.12 the manifest lists the ten pinned PyPI packages and five npm apps
(`flow` 0.3.20, `code` 0.4.2, `observer` 0.1.12, `continuum` 0.2.0, `entity` 0.1.0).

### Updating it for a release

1. Change the pins in `pyproject.toml` and the matching dictionaries in
   `abstractframework/__init__.py`.
2. Regenerate the manifest: `abstractframework manifest --write docs/installers/install-manifest.json`
   (run it from the repository checkout so it reads the edited source).
3. Check it: `abstractframework manifest --check docs/installers/install-manifest.json`. The test
   suite (`python -m pytest -q`) fails if the checked-in manifest, the pins and
   `RELEASE_VERSIONS` disagree.

## Signed artifact manifest (target design)

The rest of this page describes the manifest a future signed-installer pipeline will publish. It is
a design reference and is not generated yet.

## Release pipeline (recommended)
1. Build per-OS artifacts for each component.
2. Sign binaries and installers.
3. Notarize macOS artifacts and staple tickets.
4. Generate checksums (SHA-256) for all artifacts.
5. Publish artifacts to a trusted location (GitHub Releases or CDN).
6. Publish a signed manifest that references the artifacts.
7. Installer Manager consumes the manifest and performs updates.

## Why a manifest
- Central source of truth for available versions.
- Enables dependency resolution and compatibility checks.
- Allows stable/beta channels without manual downloads.
- Supports rollback by keeping previous versions accessible.

## Artifact manifest fields

| Field | Description |
|---|---|
| `manifest_version` | Schema version for compatibility |
| `channel` | `stable` or `beta` |
| `released_at` | ISO-8601 timestamp |
| `components` | List of components (see below) |

Each component:
| Field | Description |
|---|---|
| `id` | Stable identifier (e.g., `gateway`, `observer`) |
| `name` | User-facing name |
| `version` | Semantic version |
| `os` | Supported OS list (`mac`, `windows`, `linux`) |
| `arch` | Supported architectures |
| `download_url` | Signed artifact URL |
| `sha256` | Artifact checksum |
| `size_bytes` | Size for UX display |
| `dependencies` | Required components or plugins |
| `post_install` | Optional actions (service register, shortcuts) |

## Minimal example
```json
{
  "manifest_version": 1,
  "channel": "stable",
  "released_at": "2026-02-21T12:00:00Z",
  "components": [
    {
      "id": "gateway",
      "name": "AbstractGateway",
      "version": "0.1.0",
      "os": ["mac", "windows", "linux"],
      "arch": ["arm64", "x64"],
      "download_url": "https://example.com/abstractgateway-0.1.0.dmg",
      "sha256": "abc123...",
      "size_bytes": 123456789,
      "dependencies": ["core"],
      "post_install": ["register_service"]
    }
  ]
}
```

## Update strategy
- The manager checks the manifest on startup or on demand.
- Updates are staged, validated, and applied with health checks.
- Failed updates trigger rollback to the last known-good version.

## Security requirements
- The manifest itself should be signed.
- The manager must verify signatures and checksums before install.
- Any failed validation must stop the install, not fall back.
