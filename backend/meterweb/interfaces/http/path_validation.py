from pathlib import Path

from meterweb.infrastructure.settings import AppSettings


def normalize_upload_path(image_path: str, settings: AppSettings) -> Path:
    uploads_dir = settings.uploads_dir.resolve(strict=False)
    resolved_path = Path(image_path).resolve(strict=False)
    try:
        resolved_path.relative_to(uploads_dir)
    except ValueError as exc:
        raise ValueError(
            "Ungültiger image_path: Pfad muss innerhalb des Upload-Verzeichnisses liegen."
        ) from exc
    return resolved_path
