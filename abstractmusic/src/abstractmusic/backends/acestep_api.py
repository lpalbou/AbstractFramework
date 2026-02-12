"""
ACE-Step 1.5 REST API backend client.

This client targets the official ACE-Step v1.5 FastAPI server entry point
(`acestep-api`), which exposes endpoints like:
- POST /release_task
- POST /query_result
- GET  /v1/audio?path=...

Design notes:
- This is intentionally lightweight: the heavy ML dependencies live on the
  server-side (ACE-Step repo).
- No silent fallbacks: missing configuration raises clear errors.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


class AceStepApiError(RuntimeError):
    """Raised when the ACE-Step API returns an error or an unexpected response."""


@dataclass(frozen=True)
class AceStepApiConfig:
    base_url: str
    api_key: Optional[str] = None
    timeout_seconds: float = 600.0
    poll_interval_seconds: float = 1.0
    max_wait_seconds: float = 600.0


def _normalize_base_url(base_url: str) -> str:
    b = str(base_url or "").strip()
    if not b:
        return ""
    return b.rstrip("/")


def _auth_headers(api_key: Optional[str]) -> Dict[str, str]:
    if not isinstance(api_key, str) or not api_key.strip():
        return {}
    return {"Authorization": f"Bearer {api_key.strip()}"}


def _parse_envelope(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise AceStepApiError("Invalid response: expected JSON object envelope")
    code = payload.get("code")
    err = payload.get("error")
    if code not in (200, None):
        raise AceStepApiError(f"ACE-Step API error (code={code}): {err}")
    if err:
        raise AceStepApiError(f"ACE-Step API error: {err}")
    return payload


class AceStepApiClient:
    """Synchronous client for the ACE-Step v1.5 API server."""

    def __init__(self, *, config: AceStepApiConfig, http_client: Optional[httpx.Client] = None) -> None:
        self._config = config
        self._base_url = _normalize_base_url(config.base_url)
        if not self._base_url:
            raise ValueError("base_url is required for AceStepApiClient")

        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=float(config.timeout_seconds))

    def close(self) -> None:
        if self._owns_client:
            try:
                self._client.close()
            except Exception:
                pass

    def _url(self, path: str) -> str:
        p = str(path or "").strip()
        if not p.startswith("/"):
            p = "/" + p
        return f"{self._base_url}{p}"

    def _headers(self) -> Dict[str, str]:
        return _auth_headers(self._config.api_key)

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self._client.post(self._url(path), json=payload, headers=self._headers())
        resp.raise_for_status()
        return _parse_envelope(resp.json())

    def _get_bytes(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> bytes:
        resp = self._client.get(self._url(path), params=params, headers=self._headers())
        resp.raise_for_status()
        return bytes(resp.content)

    def release_task(self, *, prompt: str, lyrics: str = "", audio_format: str = "mp3", **kwargs: Any) -> str:
        payload: Dict[str, Any] = {
            "prompt": str(prompt or ""),
            "lyrics": str(lyrics or ""),
            "audio_format": str(audio_format or "mp3"),
        }
        # Pass through supported API params (best-effort).
        payload.update({str(k): v for k, v in kwargs.items()})

        env = self._post_json("/release_task", payload)
        data = env.get("data")
        if not isinstance(data, dict):
            raise AceStepApiError("Invalid /release_task response: missing data object")
        task_id = data.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise AceStepApiError("Invalid /release_task response: missing task_id")
        return task_id.strip()

    def query_result(self, task_id: str) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"task_id_list": [str(task_id)]}
        env = self._post_json("/query_result", payload)
        data = env.get("data")
        if not isinstance(data, list) or not data:
            raise AceStepApiError("Invalid /query_result response: expected non-empty data list")
        item = data[0]
        if not isinstance(item, dict):
            raise AceStepApiError("Invalid /query_result response: expected dict items")
        return item

    def wait_for_audio_path(self, task_id: str) -> str:
        """Poll until the job succeeds/fails/timeout, returning the server-side audio file path."""
        t0 = time.time()
        poll_s = float(self._config.poll_interval_seconds)
        max_wait_s = float(self._config.max_wait_seconds)

        while True:
            item = self.query_result(task_id)
            status = item.get("status")

            # ACE-Step v1.5 status mapping:
            # 0 -> queued/running, 1 -> succeeded, 2 -> failed
            if status == 1:
                result_raw = item.get("result")
                if not isinstance(result_raw, str) or not result_raw.strip():
                    raise AceStepApiError("Job succeeded but result is missing")
                try:
                    result_list = json.loads(result_raw)
                except Exception as e:
                    raise AceStepApiError(f"Job succeeded but result is not valid JSON: {e}") from e
                if not isinstance(result_list, list) or not result_list:
                    raise AceStepApiError("Job succeeded but result list is empty")
                first = result_list[0]
                if not isinstance(first, dict):
                    raise AceStepApiError("Job succeeded but result list items are not objects")
                path = first.get("file")
                if not isinstance(path, str) or not path.strip():
                    raise AceStepApiError("Job succeeded but no audio file path was returned")
                return path.strip()

            if status == 2:
                progress_text = item.get("progress_text")
                raise AceStepApiError(f"ACE-Step job failed: {progress_text or 'unknown error'}")

            # status == 0 (queued/running) or unknown -> keep polling
            if (time.time() - t0) > max_wait_s:
                raise AceStepApiError(f"Timed out waiting for ACE-Step job after {max_wait_s:.0f}s")
            time.sleep(max(0.1, poll_s))

    def download_audio(self, *, path: str) -> bytes:
        return self._get_bytes("/v1/audio", params={"path": str(path)})

    def t2m(self, prompt: str, *, lyrics: str = "", audio_format: str = "mp3", **kwargs: Any) -> bytes:
        task_id = self.release_task(prompt=str(prompt), lyrics=str(lyrics), audio_format=str(audio_format), **kwargs)
        audio_path = self.wait_for_audio_path(task_id)
        return self.download_audio(path=audio_path)

