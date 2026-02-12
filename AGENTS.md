## Agent Notes (AbstractFramework)

This file captures practical engineering notes discovered while evolving the codebase.

### 2026-02-12 — AbstractMusic + ACE-Step 1.5 integration

- **ACE-Step 1.5 model repo footprint**: the Hugging Face repo `ACE-Step/Ace-Step1.5` is ~9.4 GiB total and includes multiple components (DiT, LM planner, embedding model, VAE). The largest single artifact is `acestep-v15-turbo/model.safetensors` (~4.46 GiB).
- **Recommended integration pattern**: prefer ACE-Step’s **official REST API server** (`acestep-api`) and call it over HTTP from `abstractmusic`. This keeps the Abstract ecosystem lightweight and avoids pulling GPU-heavy stacks (and environment pinning) into default installs.
- **ACE-Step API endpoints used by the client**:
  - `POST /release_task` → returns `{"data": {"task_id": ...}, ...}`
  - `POST /query_result` → polls status; success returns JSON string with `file` paths
  - `GET /v1/audio?path=...` → downloads the audio bytes
- **AbstractCore capability plugins**: capability backends are discovered via the `abstractcore.capabilities_plugins` entry point group. Missing plugins must raise actionable errors (install/config hints) and we avoid silent fallbacks.

