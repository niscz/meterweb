import csv
import io

from meterweb.application.ports import ReportRenderer


class WeasyPrintReportRenderer(ReportRenderer):
    def render_pdf(self, html: str) -> bytes:
        try:
            from weasyprint import HTML
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("WeasyPrint ist nicht installiert.") from exc

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
