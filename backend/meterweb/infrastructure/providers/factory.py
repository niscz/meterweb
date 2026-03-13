import os
from dataclasses import dataclass
from pathlib import Path

from meterweb.application.ports import ChartAdapter, OCRProvider, ReportRenderer, WeatherProvider
from meterweb.infrastructure.providers.chart import ApexChartsAdapter
from meterweb.infrastructure.providers.ocr import LocalTesseractOCRProvider
from meterweb.infrastructure.providers.report import WeasyPrintReportRenderer
from meterweb.infrastructure.providers.weather import BrightSkyWeatherProvider


@dataclass(frozen=True)
class ProviderConfig:
    weather_provider: str = "brightsky"
    weather_cache_dir: str = ".cache/weather"
    ocr_provider: str = "local"
    ocr_language: str = "deu"
    chart_adapter: str = "apexcharts"
    report_renderer: str = "weasyprint"

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        return cls(
            weather_provider=os.getenv("WEATHER_PROVIDER", "brightsky"),
            weather_cache_dir=os.getenv("WEATHER_CACHE_DIR", ".cache/weather"),
            ocr_provider=os.getenv("OCR_PROVIDER", "local"),
            ocr_language=os.getenv("OCR_LANGUAGE", "deu"),
            chart_adapter=os.getenv("CHART_ADAPTER", "apexcharts"),
            report_renderer=os.getenv("REPORT_RENDERER", "weasyprint"),
        )


class ProviderFactory:
    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    def create_weather_provider(self) -> WeatherProvider:
        if self._config.weather_provider == "brightsky":
            return BrightSkyWeatherProvider(cache_dir=Path(self._config.weather_cache_dir))
        raise ValueError(f"Unbekannter Weather-Provider: {self._config.weather_provider}")

    def create_ocr_provider(self) -> OCRProvider:
        if self._config.ocr_provider == "local":
            return LocalTesseractOCRProvider(language=self._config.ocr_language)
        raise ValueError(f"Unbekannter OCR-Provider: {self._config.ocr_provider}")

    def create_chart_adapter(self) -> ChartAdapter:
        if self._config.chart_adapter == "apexcharts":
            return ApexChartsAdapter()
        raise ValueError(f"Unbekannter Chart-Adapter: {self._config.chart_adapter}")

    def create_report_renderer(self) -> ReportRenderer:
        if self._config.report_renderer == "weasyprint":
            return WeasyPrintReportRenderer()
        raise ValueError(f"Unbekannter Report-Renderer: {self._config.report_renderer}")
