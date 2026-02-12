import json

import httpx
import pytest

from abstractmusic.backends.acestep_api import AceStepApiClient, AceStepApiConfig, AceStepApiError


@pytest.mark.unit
def test_acestep_api_client_happy_path_downloads_audio_bytes():
    calls = {"release": 0, "query": 0, "audio": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/release_task":
            calls["release"] += 1
            assert request.headers.get("Authorization") == "Bearer secret"
            return httpx.Response(
                200,
                json={"data": {"task_id": "t1", "status": "queued"}, "code": 200, "error": None},
            )

        if request.url.path == "/query_result":
            calls["query"] += 1
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "task_id": "t1",
                            "status": 1,
                            "result": json.dumps([{"file": "/tmp/out.mp3"}]),
                            "progress_text": "done",
                        }
                    ],
                    "code": 200,
                    "error": None,
                },
            )

        if request.url.path == "/v1/audio":
            calls["audio"] += 1
            assert request.url.params.get("path") == "/tmp/out.mp3"
            return httpx.Response(200, content=b"mp3-bytes")

        raise AssertionError(f"Unexpected request path: {request.url.path}")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    cfg = AceStepApiConfig(base_url="http://localhost:8001", api_key="secret", poll_interval_seconds=0.01)
    client = AceStepApiClient(config=cfg, http_client=http_client)

    out = client.t2m("hello", lyrics="", audio_format="mp3")
    assert out == b"mp3-bytes"
    assert calls["release"] == 1
    assert calls["query"] == 1
    assert calls["audio"] == 1


@pytest.mark.unit
def test_acestep_api_client_raises_on_failed_job():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/release_task":
            return httpx.Response(200, json={"data": {"task_id": "t1"}, "code": 200, "error": None})
        if request.url.path == "/query_result":
            return httpx.Response(
                200,
                json={
                    "data": [{"task_id": "t1", "status": 2, "result": "[]", "progress_text": "boom"}],
                    "code": 200,
                    "error": None,
                },
            )
        raise AssertionError(f"Unexpected request path: {request.url.path}")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    cfg = AceStepApiConfig(base_url="http://localhost:8001", max_wait_seconds=1.0, poll_interval_seconds=0.01)
    client = AceStepApiClient(config=cfg, http_client=http_client)

    with pytest.raises(AceStepApiError) as e:
        client.t2m("hello")
    assert "failed" in str(e.value).lower()

