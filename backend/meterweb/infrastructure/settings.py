import os
from dataclasses import dataclass
from pathlib import Path

from meterweb.infrastructure.providers import ProviderConfig


@dataclass(frozen=True)
class AppSettings:
    weather_station_overrides_path: Path = Path("/data/weather_station_overrides.json")
    uploads_dir: Path = Path("/uploads")

    weather_provider: str = "brightsky"
    weather_cache_dir: str = ".cache/weather"
    weather_base_url: str = "https://api.brightsky.dev"
    ocr_provider: str = "local"
    ocr_language: str = "deu"
    chart_adapter: str = "apexcharts"
    report_renderer: str = "weasyprint"

    @classmethod
    def from_env(cls) -> "AppSettings":
        return cls(
            weather_station_overrides_path=Path(
                os.getenv("WEATHER_STATION_OVERRIDES_PATH", "/data/weather_station_overrides.json")
            ),
            uploads_dir=Path(os.getenv("UPLOADS_DIR", "/uploads")),
            weather_provider=os.getenv("WEATHER_PROVIDER", "brightsky"),
            weather_cache_dir=os.getenv("WEATHER_CACHE_DIR", ".cache/weather"),
            weather_base_url=os.getenv("WEATHER_BASE_URL", "https://api.brightsky.dev"),
            ocr_provider=os.getenv("OCR_PROVIDER", "local"),
            ocr_language=os.getenv("OCR_LANGUAGE", "deu"),
            chart_adapter=os.getenv("CHART_ADAPTER", "apexcharts"),
            report_renderer=os.getenv("REPORT_RENDERER", "weasyprint"),
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
