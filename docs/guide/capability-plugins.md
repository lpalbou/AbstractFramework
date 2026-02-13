# Capability plugins (Voice/Audio/Vision/Music)

This guide explains how to add optional audio/voice/vision capabilities to AbstractFramework without turning
`abstractcore` into a kitchen sink.

## Mental model (two concepts; don't mix them)

1. **LLM input modalities (AbstractCore)**
   - Attaching image/audio/video to an LLM call (`generate(..., media=[...])`) depends on the selected provider/model's
     input capabilities.

2. **Deterministic capabilities (plugins)**
   - STT/TTS and generative vision are deterministic APIs that can be used with or without an LLM call:
     - `core.voice` / `core.audio` (speech-to-text, text-to-speech) via `abstractvoice`
     - `core.vision` (text-to-image, image-to-image, ...) via `abstractvision`
     - `core.music` (text-to-music) via `abstractmusic`

This split keeps `abstractcore` lightweight by default.

## Library mode (Python)

### Install

```bash
pip install abstractcore
pip install abstractvoice      # enables core.voice + core.audio
pip install abstractvision     # enables core.vision
pip install abstractmusic      # enables core.music
```

### Discover what's available

```python
from abstractcore import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")  # example; pick a provider/model you have access to
print(llm.capabilities.status())
```

Notes:
- Capabilities load lazily the first time you access `llm.capabilities` / `llm.voice` / `llm.audio` / `llm.vision` / `llm.music`.
- Missing plugins raise an actionable error (includes an install hint).

### Use voice/audio (STT/TTS)

```python
wav_bytes = llm.voice.tts("Hello from AbstractVoice", format="wav")
open("hello.wav", "wb").write(wav_bytes)

text = llm.audio.transcribe("speech.wav")
print(text)
```

### Use generative vision (T2I/I2I/...)

`core.vision` can use an OpenAI-compatible images backend (configured via `vision_base_url` / `ABSTRACTVISION_BASE_URL`).

```python
llm = create_llm(
    "openai",
    model="gpt-4o-mini",
    vision_base_url="http://localhost:8000/v1",  # any OpenAI-compatible images endpoint
)

png_bytes = llm.vision.t2i("a red square on white background")
open("out.png", "wb").write(png_bytes)
```

### Use music generation (T2M)

`core.music` is plugin-backed (like voice/vision). `abstractmusic` provides **local in-process** generation, with **ACE-Step v1.5** as the default backend (and Diffusers audio pipelines as an alternative backend).

```python
llm = create_llm(
    # Any provider/model works here. The LLM does *not* generate music audio.
    # Music generation is performed by the configured AbstractMusic backend (ACE-Step by default).
    "ollama",
    model="qwen3:4b-instruct",
    music_backend="acestep",
    music_model_id="ACE-Step/Ace-Step1.5",
)

wav_bytes = llm.music.t2m("uplifting synthwave, 120bpm, catchy chorus", format="wav", duration_s=10.0)
open("out.wav", "wb").write(wav_bytes)
```

## Framework mode (gateway/runtime)

Install modality plugins on the durable host (the machine/process that runs the runtime + tool execution and imports
`abstractcore`), typically the AbstractGateway runner.

Thin clients (web, remote TUI) do not need `abstractvoice`/`abstractvision`/`abstractmusic` installed locally.

## Server mode (OpenAI-compatible `/v1`)

AbstractCore Server can optionally expose OpenAI-compatible endpoints by delegating to plugins:
- `/v1/images/*` (via `abstractvision`)
- `/v1/audio/*` (via the capability plugin layer, typically `abstractvoice`; plus `/v1/audio/music` when `abstractmusic` is installed)

These endpoints are interoperability-first. For durable artifact-backed outputs, prefer gateway/runtime + ArtifactStore.

