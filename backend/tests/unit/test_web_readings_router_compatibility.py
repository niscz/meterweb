import asyncio
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile

import meterweb.interfaces.http.web.readings_router as readings_router


class _FakeRepo:
    def __init__(self, register_id=None):
        self._register_id = register_id

    def get_current_register_for_meter_point(self, _meter_point_id):
        return self._register_id


class _DummyRequest:
    def __init__(self):
        self.session = {"username": "admin", "lang": "de"}
        self.query_params = {}


class _FakeListUseCase:
    def execute(self):
        return []


class _FakeAnalyticsUseCase:
    def execute(self, *_args, **_kwargs):
        return None


class _RaisingPhotoUseCase:
    def __init__(self, exc: Exception):
        self._exc = exc

    def execute(self, *_args, **_kwargs):
        raise self._exc


def test_resolve_register_id_accepts_direct_meter_register_id() -> None:
    register_id = uuid4()
    resolved = readings_router._resolve_register_id(session=None, meter_register_id=str(register_id), meter_point_id=None)
    assert resolved == register_id


def test_resolve_register_id_supports_meter_point_fallback(monkeypatch) -> None:
    register_id = uuid4()
    monkeypatch.setattr(readings_router, "SqlAlchemyReadingRepository", lambda _session: _FakeRepo(register_id))

    resolved = readings_router._resolve_register_id(session=object(), meter_register_id=None, meter_point_id=str(uuid4()))

    assert resolved == register_id


def test_resolve_register_id_raises_when_no_active_register(monkeypatch) -> None:
    monkeypatch.setattr(readings_router, "SqlAlchemyReadingRepository", lambda _session: _FakeRepo(None))

    with pytest.raises(ValueError, match="kein aktives Register"):
        readings_router._resolve_register_id(session=object(), meter_register_id=None, meter_point_id=str(uuid4()))


def test_create_photo_reading_handles_invalid_input_and_cleans_upload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(readings_router, "UPLOAD_DIR", tmp_path)
    photo = UploadFile(filename="meter.jpg", file=BytesIO(b"img"), headers={"content-type": "image/jpeg"})

    response = asyncio.run(
        readings_router.create_photo_reading(
            request=_DummyRequest(),
            meter_register_id=uuid4(),
            meter_point_id=None,
            measured_at="2025-01-01T10:00:00",
            value="invalid-number",
            photo=photo,
            add_photo_reading_use_case=_RaisingPhotoUseCase(ValueError("boom")),
            analytics_use_case=_FakeAnalyticsUseCase(),
            list_buildings=_FakeListUseCase(),
            list_units=_FakeListUseCase(),
            list_meter_points=_FakeListUseCase(),
            session=object(),
        )
    )

    assert response.template.name == "dashboard.html"
    assert response.context["reading_error"] == readings_router.translate("de", "photo_reading_invalid_input")
    assert list(tmp_path.iterdir()) == []


def test_create_photo_reading_handles_ocr_errors_and_cleans_upload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(readings_router, "UPLOAD_DIR", tmp_path)
    photo = UploadFile(filename="meter.jpg", file=BytesIO(b"img"), headers={"content-type": "image/jpeg"})

    response = asyncio.run(
        readings_router.create_photo_reading(
            request=_DummyRequest(),
            meter_register_id=uuid4(),
            meter_point_id=None,
            measured_at="2025-01-01T10:00:00",
            value="",
            photo=photo,
            add_photo_reading_use_case=_RaisingPhotoUseCase(RuntimeError("ocr down")),
            analytics_use_case=_FakeAnalyticsUseCase(),
            list_buildings=_FakeListUseCase(),
            list_units=_FakeListUseCase(),
            list_meter_points=_FakeListUseCase(),
            session=object(),
        )
    )

    assert response.template.name == "dashboard.html"
    assert response.context["reading_error"] == readings_router.translate("de", "photo_reading_ocr_failed")
    assert list(tmp_path.iterdir()) == []


async def _save_upload(router_module, upload_file: UploadFile):
    return await router_module._save_upload_streaming(upload_file)


def test_save_upload_streaming_valid_upload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(readings_router, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(readings_router, "PHOTO_UPLOAD_MAX_SIZE_BYTES", 1024)
    monkeypatch.setattr(readings_router, "ALLOWED_PHOTO_EXTENSIONS", {".jpg"})
    monkeypatch.setattr(readings_router, "ALLOWED_PHOTO_MIME_TYPES", {"image/jpeg"})
    photo = UploadFile(filename="meter.jpg", file=BytesIO(b"abc123"), headers={"content-type": "image/jpeg"})

    stored_path = asyncio.run(_save_upload(readings_router, photo))

    assert stored_path.exists()
    assert stored_path.read_bytes() == b"abc123"


def test_save_upload_streaming_rejects_too_large_files_and_cleans_up(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(readings_router, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(readings_router, "PHOTO_UPLOAD_MAX_SIZE_BYTES", 4)
    monkeypatch.setattr(readings_router, "ALLOWED_PHOTO_EXTENSIONS", {".jpg"})
    monkeypatch.setattr(readings_router, "ALLOWED_PHOTO_MIME_TYPES", {"image/jpeg"})
    photo = UploadFile(filename="meter.jpg", file=BytesIO(b"abcdef"), headers={"content-type": "image/jpeg"})

    with pytest.raises(HTTPException) as err:
        asyncio.run(_save_upload(readings_router, photo))

    assert err.value.status_code == 413
    assert list(tmp_path.iterdir()) == []


def test_save_upload_streaming_rejects_invalid_file_type(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(readings_router, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(readings_router, "PHOTO_UPLOAD_MAX_SIZE_BYTES", 1024)
    monkeypatch.setattr(readings_router, "ALLOWED_PHOTO_EXTENSIONS", {".jpg"})
    monkeypatch.setattr(readings_router, "ALLOWED_PHOTO_MIME_TYPES", {"image/jpeg"})
    photo = UploadFile(filename="meter.gif", file=BytesIO(b"gif"), headers={"content-type": "image/gif"})

    with pytest.raises(HTTPException) as err:
        asyncio.run(_save_upload(readings_router, photo))

    assert err.value.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_save_upload_streaming_cleans_up_when_upload_aborts_mid_stream(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(readings_router, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(readings_router, "PHOTO_UPLOAD_MAX_SIZE_BYTES", 1024)
    monkeypatch.setattr(readings_router, "ALLOWED_PHOTO_EXTENSIONS", {".jpg"})
    monkeypatch.setattr(readings_router, "ALLOWED_PHOTO_MIME_TYPES", {"image/jpeg"})

    photo = UploadFile(filename="meter.jpg", file=BytesIO(b"start"), headers={"content-type": "image/jpeg"})
    chunks = iter([b"part", RuntimeError("upload interrupted")])

    async def _failing_read(_size: int = -1):
        chunk = next(chunks)
        if isinstance(chunk, Exception):
            raise chunk
        return chunk

    photo.read = _failing_read

    with pytest.raises(RuntimeError, match="upload interrupted"):
        asyncio.run(_save_upload(readings_router, photo))

    assert list(tmp_path.iterdir()) == []
