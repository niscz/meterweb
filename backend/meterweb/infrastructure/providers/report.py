import csv
import io
from pathlib import Path
from typing import Any

from meterweb.application.ports import ReportRenderer


class WeasyPrintReportRenderer(ReportRenderer):
    def __init__(self, template_dir: Path | None = None) -> None:
        self._template_dir = template_dir or Path(__file__).resolve().parents[2] / "templates"

    def render_pdf_template(self, template_path: str, context: dict[str, Any]) -> bytes:
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
            from weasyprint import HTML
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("WeasyPrint und Jinja2 müssen installiert sein.") from exc

        template_env = Environment(
            loader=FileSystemLoader(str(self._template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        html = template_env.get_template(template_path).render(**context)
        return HTML(string=html).write_pdf()

    def render_xlsx(self, rows: list[dict[str, str]]) -> bytes:
        try:
            from openpyxl import Workbook
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("openpyxl ist nicht installiert.") from exc

        workbook = Workbook()
        sheet = workbook.active
        if not rows:
            sheet.append(["empty"])
        else:
            headers = list(rows[0].keys())
            sheet.append(headers)
            for row in rows:
                sheet.append([row.get(header, "") for header in headers])
        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def render_csv(self, rows: list[dict[str, str]]) -> bytes:
        buffer = io.StringIO()
        if not rows:
            buffer.write("empty\n")
        else:
            headers = list(rows[0].keys())
            writer = csv.DictWriter(buffer, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return buffer.getvalue().encode("utf-8")
