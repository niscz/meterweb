import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _import_main(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "VeryStrongSecretKeyValue123!@#AB")
    monkeypatch.setenv("ADMIN_USERNAME", "meteradmin")
    monkeypatch.setenv("ADMIN_PASSWORD", "Str0ngPassword!Test")
    sys.modules.pop("meterweb.main", None)
    return importlib.import_module("meterweb.main")


def test_readings_router_import_without_filesystem_write_access(monkeypatch) -> None:
    module_name = "meterweb.interfaces.http.web.readings_router"
    sys.modules.pop(module_name, None)

    def _deny_mkdir(self, *args, **kwargs):
        raise PermissionError("mkdir blocked")

    monkeypatch.setattr(Path, "mkdir", _deny_mkdir)

    module = importlib.import_module(module_name)

    assert module.UPLOAD_DIR is not None


def test_initialize_runtime_directories_creates_upload_dir(
    tmp_path, monkeypatch
) -> None:
    main = _import_main(monkeypatch)
    uploads_dir = tmp_path / "uploads" / "nested"
    monkeypatch.setattr(
        main,
        "get_container",
        lambda: SimpleNamespace(settings=SimpleNamespace(uploads_dir=uploads_dir)),
    )

    main.initialize_runtime_directories()

    assert uploads_dir.exists()
    assert uploads_dir.is_dir()


def test_initialize_runtime_directories_raises_config_error_on_access_failure(
    monkeypatch,
) -> None:
    main = _import_main(monkeypatch)
    blocked_uploads_dir = Path("/blocked/uploads")
    monkeypatch.setattr(
        main,
        "get_container",
        lambda: SimpleNamespace(
            settings=SimpleNamespace(uploads_dir=blocked_uploads_dir)
        ),
    )

    def _deny_mkdir(self, *args, **kwargs):
        raise PermissionError("blocked")

    monkeypatch.setattr(Path, "mkdir", _deny_mkdir)

    with pytest.raises(
        RuntimeError,
        match="Betriebsfehler: Upload-Verzeichnis kann nicht erstellt oder verwendet werden",
    ):
        main.initialize_runtime_directories()


def test_startup_calls_runtime_directory_initialization(monkeypatch) -> None:
    main = _import_main(monkeypatch)

    calls = {"init_dirs": 0, "init_db": 0}

    monkeypatch.setattr(
        main,
        "validate_runtime_security_config",
        lambda: "VeryStrongSecretKeyValue123!@#AB",
    )
    monkeypatch.setattr(main, "configure_database", lambda: None)
    monkeypatch.setattr(
        main,
        "initialize_runtime_directories",
        lambda: calls.__setitem__("init_dirs", calls["init_dirs"] + 1),
    )
    monkeypatch.setattr(
        main, "init_db", lambda: calls.__setitem__("init_db", calls["init_db"] + 1)
    )

    app = main.create_app()

    for handler in app.router.on_startup:
        handler()

    assert calls == {"init_dirs": 1, "init_db": 1}


def test_initialize_runtime_directories_uses_container_settings_even_if_env_differs(
    tmp_path, monkeypatch
) -> None:
    main = _import_main(monkeypatch)
    uploads_dir_from_container = tmp_path / "container-uploads"
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "env-uploads"))
    monkeypatch.setattr(
        main,
        "get_container",
        lambda: SimpleNamespace(
            settings=SimpleNamespace(uploads_dir=uploads_dir_from_container)
        ),
    )

    main.initialize_runtime_directories()

    assert uploads_dir_from_container.exists()
    assert not (tmp_path / "env-uploads").exists()
