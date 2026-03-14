from decimal import Decimal
from uuid import UUID

from meterweb.application.ports import ReadingRepository, ReportRenderer
from meterweb.domain.metering import consumption_from_absolute_readings


class ExportUseCase:
    def __init__(
        self,
        reading_repository: ReadingRepository,
        report_renderer: ReportRenderer,
    ) -> None:
        self._reading_repository = reading_repository
        self._report_renderer = report_renderer

    def monthly_rows(self, meter_point_id: UUID) -> list[dict[str, str]]:
        readings = self._reading_repository.list_for_meter_point(meter_point_id)
        grouped: dict[str, list] = {}
        for reading in readings:
            key = reading.measured_at.strftime("%Y-%m")
            grouped.setdefault(key, []).append(reading)

        rows: list[dict[str, str]] = []
        for month, month_readings in sorted(grouped.items()):
            consumption = Decimal("0")
            ordered = sorted(month_readings, key=lambda r: r.measured_at)
            for prev, current in zip(ordered, ordered[1:]):
                try:
                    consumption += consumption_from_absolute_readings(prev.value, current.value)
                except ValueError:
                    continue
            rows.append(
                {
                    "month": month,
                    "readings": str(len(month_readings)),
                    "consumption": str(consumption),
                }
            )
        return rows

    def export_csv(self, meter_point_id: UUID) -> bytes:
        return self._report_renderer.render_csv(self.monthly_rows(meter_point_id))

    def export_xlsx(self, meter_point_id: UUID) -> bytes:
        return self._report_renderer.render_xlsx(self.monthly_rows(meter_point_id))

    def export_pdf(self, meter_point_id: UUID) -> bytes:
        rows = self.monthly_rows(meter_point_id)
        html = "<h1>Monatsbericht</h1><table><tr><th>Monat</th><th>Ablesungen</th><th>Verbrauch</th></tr>"
        for row in rows:
            html += (
                f"<tr><td>{row['month']}</td><td>{row['readings']}"
                f"</td><td>{row['consumption']}</td></tr>"
            )
        html += "</table>"
        return self._report_renderer.render_pdf(html)
