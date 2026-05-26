# Operations and Support

This guide describes operational behavior once the installer system exists: logs,
data locations, troubleshooting, and support workflows.

## Data locations (defaults)
- AbstractCore config: `~/.abstractcore/config/`
- AbstractGateway data dir: set by installer (defaults to a user-local path)
- AbstractCode: `~/.abstractcode/`
- AbstractAssistant: `~/.abstractassistant/`
- AbstractVoice models: `~/.piper/models/`

The manager should always show the actual paths in its UI to avoid ambiguity.

## Logs
The manager should store logs in a user-visible location and provide a "Copy logs"
button for support. Each component should also expose its own logs or error reports.

## Health checks (post-install and on update)
- Gateway health endpoint reachable.
- Provider configuration valid (local server reachable or API key present).
- Optional plugins (voice/vision/music) show ready status.
- Disk space warnings for large model assets.

## Troubleshooting checklist
- **Gateway not reachable**: verify the service is running and the port is not in use.
- **Observer/Flow/Code Web cannot connect**: check gateway URL and auth token.
- **Local provider not reachable**: confirm Ollama/LM Studio is running.
- **Missing models**: use the manager to prefetch or download on demand.
- **Performance issues**: confirm GPU availability; otherwise expect CPU fallback.

## Support bundle (recommended)
The manager should be able to export a support bundle that includes:
- Version list of installed components
- Config files (redacted secrets)
- Recent logs
- Health check results

## Uninstall behavior
Uninstall should remove binaries and services but keep user data by default. The
manager must show data locations so users can delete them manually if desired.
