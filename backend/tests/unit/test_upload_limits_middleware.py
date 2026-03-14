import asyncio

from meterweb.interfaces.http.upload_limits import MultipartUploadLimitMiddleware


class _DownstreamApp:
    def __init__(self) -> None:
        self.called = False

    async def __call__(self, _scope, receive, send) -> None:
        self.called = True
        while True:
            message = await receive()
            if message["type"] == "http.request" and not message.get("more_body", False):
                break

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": b'{"ok":true}', "more_body": False})


def _make_scope(path: str, content_type: str, content_length: int | str | None) -> dict:
    headers = [(b"content-type", content_type.encode())]
    if content_length is not None:
        headers.append((b"content-length", str(content_length).encode()))

    return {
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": headers,
    }


async def _run_middleware(middleware, scope: dict, chunks: list[bytes]) -> list[dict]:
    sent: list[dict] = []
    payload = chunks.copy()

    async def _receive() -> dict:
        if payload:
            chunk = payload.pop(0)
            return {"type": "http.request", "body": chunk, "more_body": bool(payload)}
        return {"type": "http.request", "body": b"", "more_body": False}

    async def _send(message: dict) -> None:
        sent.append(message)

    await middleware(scope, _receive, _send)
    return sent


def test_upload_limit_allows_valid_multipart_request() -> None:
    downstream = _DownstreamApp()
    middleware = MultipartUploadLimitMiddleware(
        downstream,
        max_body_size_bytes=10,
        protected_paths=("/dashboard/readings/photo",),
    )

    scope = _make_scope("/dashboard/readings/photo", "multipart/form-data; boundary=abc", 5)
    sent = asyncio.run(_run_middleware(middleware, scope, [b"12345"]))

    assert downstream.called is True
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 200


def test_upload_limit_rejects_oversized_request_before_endpoint() -> None:
    downstream = _DownstreamApp()
    middleware = MultipartUploadLimitMiddleware(
        downstream,
        max_body_size_bytes=4,
        protected_paths=("/dashboard/readings/photo",),
    )

    scope = _make_scope("/dashboard/readings/photo", "multipart/form-data; boundary=abc", 5)
    sent = asyncio.run(_run_middleware(middleware, scope, [b"12345"]))

    assert downstream.called is False
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413


def test_upload_limit_only_applies_to_configured_paths() -> None:
    downstream = _DownstreamApp()
    middleware = MultipartUploadLimitMiddleware(
        downstream,
        max_body_size_bytes=4,
        protected_paths=("/dashboard/readings/photo",),
    )

    scope = _make_scope("/dashboard/readings", "multipart/form-data; boundary=abc", 5)
    sent = asyncio.run(_run_middleware(middleware, scope, [b"12345"]))

    assert downstream.called is True
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 200


def test_upload_limit_rejects_invalid_content_length_header() -> None:
    downstream = _DownstreamApp()
    middleware = MultipartUploadLimitMiddleware(
        downstream,
        max_body_size_bytes=10,
        protected_paths=("/dashboard/readings/photo",),
    )

    scope = _make_scope("/dashboard/readings/photo", "multipart/form-data; boundary=abc", "abc")
    sent = asyncio.run(_run_middleware(middleware, scope, [b"12345"]))

    assert downstream.called is False
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 400


def test_upload_limit_rejects_oversized_stream_without_content_length_header() -> None:
    downstream = _DownstreamApp()
    middleware = MultipartUploadLimitMiddleware(
        downstream,
        max_body_size_bytes=4,
        protected_paths=("/dashboard/readings/photo",),
    )

    scope = _make_scope("/dashboard/readings/photo", "multipart/form-data; boundary=abc", None)
    sent = asyncio.run(_run_middleware(middleware, scope, [b"123", b"45"]))

    assert downstream.called is True
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413
