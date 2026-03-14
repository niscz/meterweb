from meterweb.infrastructure.providers import ProviderConfig, ProviderFactory
from meterweb.infrastructure.providers.chart import ApexChartsAdapter
from meterweb.infrastructure.providers.ocr import LocalTesseractOCRProvider
from meterweb.infrastructure.providers.report import WeasyPrintReportRenderer
from meterweb.infrastructure.providers.weather import BrightSkyWeatherProvider


def test_provider_factory_creates_configured_providers(tmp_path) -> None:
    config = ProviderConfig(weather_cache_dir=str(tmp_path), weather_base_url="https://weather.example")
    factory = ProviderFactory(config)

    weather_provider = factory.create_weather_provider()

    assert isinstance(weather_provider, BrightSkyWeatherProvider)
    assert weather_provider._base_url == "https://weather.example"
    assert isinstance(factory.create_ocr_provider(), LocalTesseractOCRProvider)
    assert isinstance(factory.create_chart_adapter(), ApexChartsAdapter)
    assert isinstance(factory.create_report_renderer(), WeasyPrintReportRenderer)
