# AbstractMusic

`abstractmusic` is a lightweight, backend-agnostic **text-to-music** library designed to plug into **AbstractCore** as an optional capability plugin.

## Quickstart (AbstractCore integration)

1. Run an ACE-Step 1.5 API server (recommended approach for local generation):
   - In the ACE-Step-1.5 repo: `uv run acestep-api` (default `http://127.0.0.1:8001`)
2. Configure and call from AbstractCore:

```python
from abstractcore import create_llm

llm = create_llm(
    # Any provider/model works here. The LLM does *not* generate music audio.
    # Music generation is performed by the configured AbstractMusic backend (ACE-Step API in v0).
    "ollama",
    model="qwen3:4b-instruct",
    music_base_url="http://127.0.0.1:8001",
)

mp3_bytes = llm.music.t2m("uplifting synthwave, 120bpm, catchy chorus", format="mp3")
open("out.mp3", "wb").write(mp3_bytes)
```

## Notes

- `abstractmusic` does **not** bundle ACE-Step’s GPU-heavy, tightly-pinned inference stack by default. For v0 it acts as a client to ACE-Step’s official REST API server (`acestep-api`).
- When used in framework mode (gateway/runtime), outputs can be stored durably via an ArtifactStore (returns an `{"$artifact": ...}` ref).

