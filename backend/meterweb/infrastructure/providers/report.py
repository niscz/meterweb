from meterweb.application.ports import ReportRenderer


class WeasyPrintReportRenderer(ReportRenderer):
    def render_pdf(self, html: str) -> bytes:
        try:
            from weasyprint import HTML
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("WeasyPrint ist nicht installiert.") from exc

        return HTML(string=html).write_pdf()
