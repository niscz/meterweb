import os
from dataclasses import dataclass
from pathlib import Path

from meterweb.infrastructure.providers import ProviderConfig


@dataclass(frozen=True)
class AppSettings:
    weather_station_overrides_path: Path = Path("/data/weather_station_overrides.json")
    uploads_dir: Path = Path("/uploads")
    photo_upload_max_size_bytes: int = 10 * 1024 * 1024
    photo_upload_allowed_mime_types: tuple[str, ...] = ("image/jpeg", "image/png", "image/webp")
    photo_upload_allowed_extensions: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".webp")

    weather_provider: str = "brightsky"
    weather_cache_dir: str = ".cache/weather"
    weather_base_url: str = "https://api.brightsky.dev"
    ocr_provider: str = "local"
    ocr_language: str = "deu"
    chart_adapter: str = "apexcharts"
    report_renderer: str = "weasyprint"
    login_max_attempts: int = 5
    login_attempt_window_seconds: int = 300
    login_lock_duration_seconds: int = 300
    trust_proxy_headers: bool = False
    trusted_proxy_ips: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> "AppSettings":
        return cls(
            weather_station_overrides_path=Path(
                os.getenv("WEATHER_STATION_OVERRIDES_PATH", "/data/weather_station_overrides.json")
            ),
            uploads_dir=Path(os.getenv("UPLOADS_DIR", "/uploads")),
            photo_upload_max_size_bytes=_env_int("PHOTO_UPLOAD_MAX_SIZE_BYTES", 10 * 1024 * 1024),
            photo_upload_allowed_mime_types=_env_list(
                "PHOTO_UPLOAD_ALLOWED_MIME_TYPES",
                ("image/jpeg", "image/png", "image/webp"),
            ),
            photo_upload_allowed_extensions=_normalize_extensions(
                _env_list("PHOTO_UPLOAD_ALLOWED_EXTENSIONS", (".jpg", ".jpeg", ".png", ".webp"))
            ),
            weather_provider=os.getenv("WEATHER_PROVIDER", "brightsky"),
            weather_cache_dir=os.getenv("WEATHER_CACHE_DIR", ".cache/weather"),
            weather_base_url=os.getenv("WEATHER_BASE_URL", "https://api.brightsky.dev"),
            ocr_provider=os.getenv("OCR_PROVIDER", "local"),
            ocr_language=os.getenv("OCR_LANGUAGE", "deu"),
            chart_adapter=os.getenv("CHART_ADAPTER", "apexcharts"),
            report_renderer=os.getenv("REPORT_RENDERER", "weasyprint"),
            login_max_attempts=_env_int("LOGIN_MAX_ATTEMPTS", 5),
            login_attempt_window_seconds=_env_int("LOGIN_ATTEMPT_WINDOW_SECONDS", 300),
            login_lock_duration_seconds=_env_int("LOGIN_LOCK_DURATION_SECONDS", 300),
            trust_proxy_headers=_env_bool("TRUST_PROXY_HEADERS", False),
            trusted_proxy_ips=_env_list("TRUSTED_PROXY_IPS", ()) if os.getenv("TRUSTED_PROXY_IPS") else (),
        )

    def provider_config(self) -> ProviderConfig:
        return ProviderConfig(
            weather_provider=self.weather_provider,
            weather_cache_dir=self.weather_cache_dir,
            weather_base_url=self.weather_base_url,
            ocr_provider=self.ocr_provider,
            ocr_language=self.ocr_language,
            chart_adapter=self.chart_adapter,
            report_renderer=self.report_renderer,
        )


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = int(raw)
    if value <= 0:
        raise RuntimeError(f"Environment variable {name} must be greater than 0")
    return value


def _env_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if raw is None:
        return default
    values = tuple(part.strip().lower() for part in raw.split(",") if part.strip())
    if not values:
        raise RuntimeError(f"Environment variable {name} must not be empty")
    return values


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"Environment variable {name} must be a boolean value")


def _normalize_extensions(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(value if value.startswith(".") else f".{value}" for value in values)
    if not normalized:
        raise RuntimeError("PHOTO_UPLOAD_ALLOWED_EXTENSIONS must not be empty")
    return normalized
