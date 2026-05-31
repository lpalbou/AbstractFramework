# Installer And Setup Track

This proposed track collects follow-up work for turning the current AbstractFramework install
experience into a production-grade setup system for both technical and non-technical users.

The items are grouped because they share the same boundary: `abstractframework` should remain the
Python release profile and install contract, while native installer applications should consume
that contract rather than duplicating pins by hand.

Recommended reading order:

1. `../../completed/0158_installer_repository_extraction.md`
2. `../../completed/0159_generated_install_manifest_contract.md`
3. `../../completed/0160_framework_doctor_and_launch_cli.md`
4. `../../completed/0161_three_path_public_install_guide.md`
5. `0162_signed_installer_ci_and_distribution.md`
6. `0163_cpu_local_inference_install_profile.md`

Relevant docs and decisions:

- `docs/installers/`
- `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
- `docs/adr/0034-framework-release-sequence-and-gates.md`
- `docs/adr/reorg/2026-02-21_installer_manager_strategy.md`
- `docs/adr/reorg/2026-02-21_macos_installer_manager.md`
- `https://github.com/lpalbou/AbstractInstallers`

Non-goals for this proposed track:

- Do not make the root `abstractframework` wheel ship native installer source or binaries.
- Do not make installers own package version pins independently from the root release profile.
- Do not bypass OS signing, notarization, or checksum requirements for production artifacts.
- Do not add a CPU local profile until each package's CPU backend story is audited.
