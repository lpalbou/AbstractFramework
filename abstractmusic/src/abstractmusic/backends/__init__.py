"""
Backend implementations for AbstractMusic.

Backends are responsible for turning user prompts into audio bytes (or durable
artifact references when running under an ArtifactStore).
"""

from __future__ import annotations

__all__ = [
    "AceStepApiClient",
    "AceStepApiConfig",
    "AceStepApiError",
]

from .acestep_api import AceStepApiClient, AceStepApiConfig, AceStepApiError

