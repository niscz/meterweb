from meterweb.infrastructure.providers import ProviderConfig, ProviderFactory
from meterweb.infrastructure.providers.chart import ApexChartsAdapter
from meterweb.infrastructure.providers.ocr import LocalTesseractOCRProvider
from meterweb.infrastructure.providers.report import WeasyPrintReportRenderer
from meterweb.infrastructure.providers.weather import BrightSkyWeatherProvider


def test_provider_factory_creates_configured_providers(tmp_path) -> None:
    config = ProviderConfig(weather_cache_dir=str(tmp_path))
    factory = ProviderFactory(config)

    assert isinstance(factory.create_weather_provider(), BrightSkyWeatherProvider)
    assert isinstance(factory.create_ocr_provider(), LocalTesseractOCRProvider)
    assert isinstance(factory.create_chart_adapter(), ApexChartsAdapter)
    assert isinstance(factory.create_report_renderer(), WeasyPrintReportRenderer)
