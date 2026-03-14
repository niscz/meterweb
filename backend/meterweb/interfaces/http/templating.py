from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from fastapi import Request
from fastapi.templating import Jinja2Templates

from meterweb.interfaces.http.common import get_csrf_token, get_locale, translate


def _to_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def format_number(value: object, lang: str) -> str:
    number = _to_decimal(value)
    raw = format(number, "f")
    if "." in raw:
        int_part, frac_part = raw.split(".", 1)
        frac_part = frac_part.rstrip("0")
    else:
        int_part, frac_part = raw, ""

    sign = ""
    if int_part.startswith("-"):
        sign = "-"
        int_part = int_part[1:]

    chunks: list[str] = []
    while int_part:
        chunks.append(int_part[-3:])
        int_part = int_part[:-3]
    thousands_sep = "." if lang == "de" else ","
    decimal_sep = "," if lang == "de" else "."
    grouped = thousands_sep.join(reversed(chunks)) if chunks else "0"
    if frac_part:
        return f"{sign}{grouped}{decimal_sep}{frac_part}"
    return f"{sign}{grouped}"


def format_month(month_key: str, lang: str) -> str:
    try:
        month_date = datetime.strptime(month_key, "%Y-%m")
    except ValueError:
        return month_key
    return month_date.strftime("%m.%Y") if lang == "de" else month_date.strftime("%Y-%m")


def format_date_value(value: object, lang: str) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y") if lang == "de" else value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y") if lang == "de" else value.strftime("%Y-%m-%d")
    return str(value)


def localize_monthly_rows(rows: list[dict[str, str]], lang: str) -> list[dict[str, str]]:
    localized: list[dict[str, str]] = []
    for row in rows:
        localized.append(
            {
                "month": format_month(row["month"], lang),
                "readings": format_number(row["readings"], lang),
                "consumption": format_number(row["consumption"], lang),
            }
        )
    return localized


def _context_translator(lang: str) -> Callable[[str], str]:
    return lambda key: translate(lang, key)


def i18n_context(request: Request) -> dict[str, object]:
    lang = get_locale(request)
    return {
        "lang": lang,
        "t": _context_translator(lang),
        "fmt_number": lambda value: format_number(value, lang),
        "fmt_month": lambda value: format_month(value, lang),
        "fmt_date": lambda value: format_date_value(value, lang),
        "csrf_token": get_csrf_token(request),
    }


def create_templates() -> Jinja2Templates:
    return Jinja2Templates(directory="meterweb/templates", context_processors=[i18n_context])
