from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class _PayloadTooLarge(Exception):
    pass


class MultipartUploadLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        max_body_size_bytes: int,
        protected_paths: tuple[str, ...],
    ) -> None:
        self.app = app
        self.max_body_size_bytes = max_body_size_bytes
        self.protected_paths = protected_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self._should_enforce(scope):
            await self.app(scope, receive, send)
            return

        headers = Headers(raw=scope.get("headers", []))
        content_length = headers.get("content-length")
        if content_length is not None and int(content_length) > self.max_body_size_bytes:
            await self._send_too_large(scope, send)
            return

        total_received = 0

        async def limited_receive() -> Message:
            nonlocal total_received
            message = await receive()
            if message["type"] != "http.request":
                return message
            body = message.get("body", b"")
            total_received += len(body)
            if total_received > self.max_body_size_bytes:
                raise _PayloadTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _PayloadTooLarge:
            await self._send_too_large(scope, send)

    def _should_enforce(self, scope: Scope) -> bool:
        if scope["type"] != "http":
            return False

        method = scope.get("method", "").upper()
        if method not in {"POST", "PUT", "PATCH"}:
            return False

        if scope.get("path") not in self.protected_paths:
            return False

        headers = Headers(raw=scope.get("headers", []))
        content_type = headers.get("content-type", "").lower()
        return content_type.startswith("multipart/form-data")

    async def _send_too_large(self, scope: Scope, send: Send) -> None:
        response = JSONResponse(status_code=413, content={"detail": "Datei ist zu groß."})

        async def _noop_receive() -> Message:
            return {"type": "http.request", "body": b"", "more_body": False}

        await response(scope, _noop_receive, send)
