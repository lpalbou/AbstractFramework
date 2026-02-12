"""
AbstractCore capability plugin for AbstractMusic.

This registers a `music` capability backend discovered by AbstractCore via the
`abstractcore.capabilities_plugins` entry point group.

Backend (v0):
- ACE-Step 1.5 via its official REST API server (`acestep-api`).
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from ..artifacts import RuntimeArtifactStoreAdapter
from ..backends.acestep_api import AceStepApiClient, AceStepApiConfig


def _content_type_for_audio_format(fmt: str) -> str:
    f = str(fmt or "").strip().lower()
    if f == "wav":
        return "audio/wav"
    if f == "flac":
        return "audio/flac"
    if f == "ogg":
        return "audio/ogg"
    # Default: mp3
    return "audio/mpeg"


def _resolve_config(owner: Any) -> AceStepApiConfig:
    cfg = getattr(owner, "config", None)

    base_url = None
    api_key = None
    timeout_s = None
    poll_s = None
    max_wait_s = None

    if isinstance(cfg, dict):
        base_url = cfg.get("music_base_url") or cfg.get("acestep_base_url") or cfg.get("acestep_api_base_url")
        api_key = cfg.get("music_api_key") or cfg.get("acestep_api_key")
        timeout_s = cfg.get("music_timeout_seconds")
        poll_s = cfg.get("music_poll_interval_seconds")
        max_wait_s = cfg.get("music_max_wait_seconds")

    base_url = (
        base_url
        or os.getenv("ABSTRACTMUSIC_BASE_URL")
        or os.getenv("ABSTRACTMUSIC_ACESTEP_BASE_URL")
        or os.getenv("ACESTEP_API_BASE_URL")
    )
    api_key = api_key or os.getenv("ABSTRACTMUSIC_API_KEY") or os.getenv("ABSTRACTMUSIC_ACESTEP_API_KEY")

    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError(
            "ACE-Step API base URL is not configured. "
            "Set ABSTRACTMUSIC_BASE_URL or pass music_base_url='http://127.0.0.1:8001' to create_llm(...)."
        )

    return AceStepApiConfig(
        base_url=str(base_url).strip(),
        api_key=str(api_key).strip() if isinstance(api_key, str) and api_key.strip() else None,
        timeout_seconds=float(timeout_s) if timeout_s is not None else 600.0,
        poll_interval_seconds=float(poll_s) if poll_s is not None else 1.0,
        max_wait_seconds=float(max_wait_s) if max_wait_s is not None else 600.0,
    )


class _AceStepApiMusicCapability:
    """AbstractCore `music` capability backed by an ACE-Step REST API server."""

    backend_id = "abstractmusic:acestep-api"

    def __init__(self, owner: Any) -> None:
        self._owner = owner
        self._cfg = _resolve_config(owner)
        self._client = AceStepApiClient(config=self._cfg)

    def t2m(
        self,
        prompt: str,
        *,
        lyrics: Optional[str] = None,
        format: str = "mp3",
        artifact_store: Any = None,
        run_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        fmt = str(format or "mp3").strip().lower() or "mp3"
        audio_bytes = self._client.t2m(
            str(prompt or ""),
            lyrics=str(lyrics or ""),
            audio_format=fmt,
            **kwargs,
        )

        if artifact_store is None:
            return bytes(audio_bytes)

        store = RuntimeArtifactStoreAdapter(artifact_store)
        merged_tags: Dict[str, str] = {"kind": "generated_media", "modality": "audio", "task": "text2music"}
        if isinstance(tags, dict):
            merged_tags.update({str(k): str(v) for k, v in tags.items()})

        return store.store_bytes(
            bytes(audio_bytes),
            content_type=_content_type_for_audio_format(fmt),
            filename=f"music.{fmt}",
            run_id=str(run_id) if run_id else None,
            tags=merged_tags,
            metadata=metadata if isinstance(metadata, dict) else None,
        )


def register(registry: Any) -> None:
    """Register AbstractMusic as an AbstractCore capability plugin."""

    config_hint = (
        "Run an ACE-Step 1.5 API server (default http://127.0.0.1:8001), then set "
        "ABSTRACTMUSIC_BASE_URL or pass music_base_url=... to create_llm(...). "
        "ACE-Step server: in ACE-Step-1.5 repo run `uv run acestep-api`."
    )

    registry.register_music_backend(
        backend_id=_AceStepApiMusicCapability.backend_id,
        factory=lambda owner: _AceStepApiMusicCapability(owner),
        priority=0,
        description="ACE-Step 1.5 via ACE-Step REST API server (acestep-api).",
        config_hint=config_hint,
    )

