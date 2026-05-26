# User Journeys (Step-by-step)

These flows describe how the installer should behave for AbstractFramework users.

## Full framework install (recommended)
1. Download the Installer Manager for your OS and launch it.
2. Select **Install full framework**.
3. Review default components:
   - AbstractGateway (required)
   - AbstractObserver, AbstractFlow, AbstractCode Web
   - AbstractCode (terminal)
   - Optional: AbstractAssistant, SmartNote (only if supported on your OS)
4. Choose a data directory (default shown) and confirm ports.
5. Pick a provider path:
   - **Local**: detect Ollama or LM Studio; if missing, show install link.
   - **Cloud**: enter API keys; store in config (not env vars).
6. Optional: enable Voice/Vision/Music; confirm model download sizes.
7. Install: download packages, verify checksums, and register services.
8. Post-install checks: verify gateway health, provider reachability, and model readiness.
9. Launch: open Observer, Flow Editor, and Code Web; show shortcuts in the manager.

## Install a single app (example: AbstractCode)
1. Choose **Install a single app** and select **AbstractCode**.
2. Decide on runtime mode:
   - Local-only (no gateway)
   - Gateway-first (connect to a gateway you select or install)
3. Choose provider (local or cloud) and complete configuration.
4. Install and launch AbstractCode from the manager.

## Install the gateway + browser UIs only
1. Choose **Custom install** and select:
   - AbstractGateway
   - AbstractObserver
   - AbstractFlow
   - AbstractCode Web
2. Set gateway token and data directory.
3. Install and start the gateway service.
4. Launch each UI with the gateway URL preconfigured.

## Update flow
1. Manager checks for updates (stable/beta channel).
2. User reviews release notes and approves update.
3. Manager downloads and verifies new packages.
4. Manager performs a safe restart of services.
5. If health checks fail, rollback to the last known-good version.

## Repair flow
1. User selects **Repair** for a component.
2. Manager revalidates checksums and config files.
3. Manager reinstalls the component if needed.
4. Manager runs health checks and reports status.

## Uninstall flow
1. User selects **Uninstall** for a component.
2. Manager confirms whether to keep data (default: keep).
3. Manager removes binaries and services.
4. Manager shows data locations for manual cleanup if desired.

## Offline / airgapped flow
1. Download an offline bundle (manager + packages + manifest).
2. Transfer to the offline machine.
3. Run the manager from the offline bundle.
4. Install selected components without network access.
