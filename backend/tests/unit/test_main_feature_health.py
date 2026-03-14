import importlib

from fastapi.testclient import TestClient


def test_health_features_endpoint_exposes_feature_flags(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "VeryStrongSecretKeyValue123!@#AB")
    monkeypatch.setenv("ADMIN_USERNAME", "meteradmin")
    monkeypatch.setenv("ADMIN_PASSWORD", "Str0ngPassword!Test")

    main = importlib.import_module("meterweb.main")
    monkeypatch.setattr(main, "validate_runtime_security_config", lambda: "VeryStrongSecretKeyValue123!@#AB")
    monkeypatch.setattr(main, "configure_database", lambda: None)
    monkeypatch.setattr(main, "_feature_flags", lambda: {"ocr": {"enabled": False, "missing": ["system:tesseract-ocr"]}})

    app = main.create_app()
    client = TestClient(app)

    response = client.get("/health/features")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "features": {"ocr": {"enabled": False, "missing": ["system:tesseract-ocr"]}},
    }


def test_feature_flags_disable_reports_when_import_fails(monkeypatch) -> None:
    main = importlib.import_module("meterweb.main")

    real_import_module = importlib.import_module

    def _fake_import_module(name: str):
        if name == "weasyprint":
            raise OSError("missing cairo")
        return real_import_module(name)

    monkeypatch.setattr(main.importlib, "import_module", _fake_import_module)
    monkeypatch.setattr(main.shutil, "which", lambda _name: "/usr/bin/tesseract")

    features = main._feature_flags()

    assert features["reports"]["enabled"] is False
    assert features["reports"]["missing"] == ["python:weasyprint/openpyxl"]
