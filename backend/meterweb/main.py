import importlib
import logging
import os
import shutil

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from meterweb.bootstrap import get_container
from meterweb.infrastructure.auth import validate_runtime_security_config
from meterweb.infrastructure.db import configure_database, init_db
from meterweb.interfaces.http.errors import register_exception_handlers
from meterweb.interfaces.http.router import router


def _get_env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _feature_flags() -> dict[str, dict[str, object]]:
    def _import_optional_modules(*modules: str) -> tuple[bool, list[str]]:
        missing: list[str] = []
        for module in modules:
            try:
                importlib.import_module(module)
            except Exception:
                missing.append(module)
        return len(missing) == 0, missing

    ocr_python_ready, _ = _import_optional_modules("cv2", "pytesseract", "PIL")
    tesseract_binary = shutil.which("tesseract") is not None
    reports_python_ready, _ = _import_optional_modules("weasyprint", "openpyxl")

    return {
        "ocr": {
            "enabled": ocr_python_ready and tesseract_binary,
            "missing": [
                *(
                    []
                    if ocr_python_ready
                    else ["python:opencv-python-headless/pytesseract/Pillow"]
                ),
                *([] if tesseract_binary else ["system:tesseract-ocr"]),
            ],
        },
        "reports": {
            "enabled": reports_python_ready,
            "missing": [] if reports_python_ready else ["python:weasyprint/openpyxl"],
        },
    }


def initialize_runtime_directories() -> None:
    uploads_dir = get_container().settings.uploads_dir
    try:
        uploads_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            "Betriebsfehler: Upload-Verzeichnis kann nicht erstellt oder verwendet werden: "
            f"{uploads_dir}"
        ) from exc


def create_app() -> FastAPI:
    configure_database()

    secret_key = validate_runtime_security_config()

    app = FastAPI(title="meterweb")

    session_options = {
        "secret_key": secret_key,
        "same_site": "strict",
        "https_only": _get_env_bool("SESSION_HTTPS_ONLY", default=True),
        "max_age": int(os.getenv("SESSION_MAX_AGE", "3600")),
        "path": os.getenv("SESSION_COOKIE_PATH", "/"),
    }
    session_domain = os.getenv("SESSION_COOKIE_DOMAIN")
    if session_domain:
        session_options["domain"] = session_domain

    app.add_middleware(SessionMiddleware, **session_options)
    register_exception_handlers(app)
    app.include_router(router)

    @app.get("/health/features", tags=["health"])
    def health_features() -> dict[str, object]:
        features = _feature_flags()
        return {
            "status": "ok",
            "features": features,
        }

    @app.on_event("startup")
    def _startup() -> None:
        initialize_runtime_directories()
        init_db()
        features = _feature_flags()
        logger = logging.getLogger("meterweb.startup")
        for feature_name, result in features.items():
            if result["enabled"]:
                logger.info("Feature '%s' aktiviert", feature_name)
            else:
                logger.warning(
                    "Feature '%s' nicht vollständig verfügbar. Fehlend: %s",
                    feature_name,
                    ", ".join(result["missing"]),
                )

    return app


app = create_app()
