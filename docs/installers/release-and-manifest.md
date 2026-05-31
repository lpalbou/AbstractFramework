# Release Pipeline and Manifest

This guide describes how installer artifacts are built, signed, and published, plus
the manifest format the Installer Manager uses to discover components. The current
profile manifest is generated from the root `abstractframework` release pins:

```bash
abstractframework manifest --check docs/installers/install-manifest.json
```

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

## Manifest schema (core fields)

The checked-in schema lives at `install-manifest.schema.json`. The generated release
manifest lives at `install-manifest.json`.

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
