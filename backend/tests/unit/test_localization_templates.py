from pathlib import Path
from decimal import Decimal

from jinja2 import Environment, FileSystemLoader

from meterweb.interfaces.http.common import translate
from meterweb.interfaces.http.templating import format_month, format_number


def _render_template(path: str, lang: str) -> str:
    template_dir = Path(__file__).resolve().parents[2] / "meterweb" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template(path)
    return template.render(
        lang=lang,
        rows=[{"month": "2025-01", "readings": "12", "consumption": "1234.5"}],
        meter_point_id="00000000-0000-0000-0000-000000000000",
        t=lambda key: translate(lang, key),
        fmt_number=lambda value: format_number(value, lang),
        fmt_month=lambda value: format_month(value, lang),
    )


def test_monthly_report_template_golden_de() -> None:
    rendered = _render_template("monthly_report.html", "de")

    assert "Monatsbericht je Objekt" in rendered
    assert "<th>Monat</th>" in rendered
    assert "<td>01.2025</td>" in rendered
    assert "<td>1.234,5</td>" in rendered


def test_monthly_report_template_golden_en() -> None:
    rendered = _render_template("monthly_report.html", "en")

    assert "Monthly report by object" in rendered
    assert "<th>Month</th>" in rendered
    assert "<td>2025-01</td>" in rendered
    assert "<td>1,234.5</td>" in rendered


def test_monthly_report_pdf_template_golden_de_and_en() -> None:
    rendered_de = _render_template("reports/monthly_report_pdf.html", "de")
    rendered_en = _render_template("reports/monthly_report_pdf.html", "en")

    assert '<html lang="de">' in rendered_de
    assert "Monatsbericht je Objekt" in rendered_de
    assert "<td>1.234,5</td>" in rendered_de

    assert '<html lang="en">' in rendered_en
    assert "Monthly report by object" in rendered_en
    assert "<td>1,234.5</td>" in rendered_en


def test_format_number_handles_large_integral_decimals() -> None:
    large = Decimal("999999999999999999999999999999")

    assert format_number(large, "en") == "999,999,999,999,999,999,999,999,999,999"
    assert format_number(large, "de") == "999.999.999.999.999.999.999.999.999.999"


def test_format_number_handles_exponent_integral_decimals() -> None:
    large_exponent = Decimal("1E+30")

    assert format_number(large_exponent, "en") == "1,000,000,000,000,000,000,000,000,000,000"
    assert format_number(large_exponent, "de") == "1.000.000.000.000.000.000.000.000.000.000"
