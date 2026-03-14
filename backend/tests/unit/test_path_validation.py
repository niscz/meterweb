from pathlib import Path

import pytest

from meterweb.infrastructure.settings import AppSettings
from meterweb.interfaces.http.path_validation import normalize_upload_path


def test_normalize_upload_path_accepts_path_within_upload_dir(tmp_path: Path) -> None:
    settings = AppSettings(uploads_dir=tmp_path / "uploads")
    nested = settings.uploads_dir / "images" / "meter.jpg"

    result = normalize_upload_path(str(nested), settings)

    assert result == nested.resolve()


def test_normalize_upload_path_rejects_traversal_outside_upload_dir(tmp_path: Path) -> None:
    settings = AppSettings(uploads_dir=tmp_path / "uploads")

    with pytest.raises(ValueError, match="innerhalb des Upload-Verzeichnisses"):
        normalize_upload_path(str(settings.uploads_dir / ".." / "escape.jpg"), settings)
