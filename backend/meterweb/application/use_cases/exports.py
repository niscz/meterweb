from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from meterweb.application.ports import ReadingRepository, ReportRenderer
from meterweb.domain.metering import Reading, consumption_from_absolute_readings


class ExportUseCase:
    def __init__(
        self,
        reading_repository: ReadingRepository,
        report_renderer: ReportRenderer,
    ) -> None:
        self._reading_repository = reading_repository
        self._report_renderer = report_renderer

    def monthly_rows_for_meter_register(self, meter_register_id: UUID) -> list[dict[str, str]]:
        return _monthly_rows(self._reading_repository.list_for_meter_register(meter_register_id))

    def monthly_rows_for_meter_point(self, meter_point_id: UUID) -> list[dict[str, str]]:
        return _monthly_rows(self._reading_repository.list_for_meter_point(meter_point_id))

    def monthly_rows_for_building(self, building_id: UUID) -> list[dict[str, str]]:
        return _monthly_rows(self._reading_repository.list_for_building(building_id))

    def monthly_rows(self, meter_point_id: UUID) -> list[dict[str, str]]:
        return self.monthly_rows_for_meter_point(meter_point_id)

    def export_csv_for_meter_register(self, meter_register_id: UUID) -> bytes:
        return self._report_renderer.render_csv(self.monthly_rows_for_meter_register(meter_register_id))

    def export_xlsx_for_meter_register(self, meter_register_id: UUID) -> bytes:
        return self._report_renderer.render_xlsx(self.monthly_rows_for_meter_register(meter_register_id))

    def export_pdf_for_meter_register(self, meter_register_id: UUID, lang: str = "de") -> bytes:
        rows = self.monthly_rows_for_meter_register(meter_register_id)
        return self._report_renderer.render_pdf_template("reports/monthly_report_pdf.html", {"rows": rows, "lang": lang})

    def export_csv_for_building(self, building_id: UUID) -> bytes:
        return self._report_renderer.render_csv(self.monthly_rows_for_building(building_id))

    def export_xlsx_for_building(self, building_id: UUID) -> bytes:
        return self._report_renderer.render_xlsx(self.monthly_rows_for_building(building_id))

    def export_pdf_for_building(self, building_id: UUID, lang: str = "de") -> bytes:
        rows = self.monthly_rows_for_building(building_id)
        return self._report_renderer.render_pdf_template("reports/monthly_report_pdf.html", {"rows": rows, "lang": lang})

    def export_csv(self, meter_point_id: UUID) -> bytes:
        return self._report_renderer.render_csv(self.monthly_rows_for_meter_point(meter_point_id))

    def export_xlsx(self, meter_point_id: UUID) -> bytes:
        return self._report_renderer.render_xlsx(self.monthly_rows_for_meter_point(meter_point_id))

    def export_pdf(self, meter_point_id: UUID, lang: str = "de") -> bytes:
        rows = self.monthly_rows_for_meter_point(meter_point_id)
        return self._report_renderer.render_pdf_template(
            "reports/monthly_report_pdf.html",
            {"rows": rows, "lang": lang},
        )


def _monthly_rows(readings: list[Reading]) -> list[dict[str, str]]:
    # Fachliche Regel für die Monatszuordnung:
    # Verbrauch wird immer aus zwei aufeinanderfolgenden absoluten Readings desselben Registers
    # berechnet (prev -> current) und vollständig dem Monat des `current.measured_at`
    # zugeordnet. Dadurch ist die Logik für Register-, Meter-Point- und Building-Exports
    # identisch und liefert konsistente Werte für CSV/XLSX/PDF.
    grouped: dict[str, list[Reading]] = {}
    for reading in readings:
        key = reading.measured_at.strftime("%Y-%m")
        grouped.setdefault(key, []).append(reading)

    consumption_by_month: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    by_register: dict[UUID, list[Reading]] = defaultdict(list)
    for reading in readings:
        by_register[reading.meter_register_id].append(reading)

    for register_readings in by_register.values():
        ordered = sorted(register_readings, key=lambda r: (r.measured_at, r.id))
        for prev, current in zip(ordered, ordered[1:]):
            try:
                delta = consumption_from_absolute_readings(prev.value, current.value)
            except ValueError:
                continue
            month_key = current.measured_at.strftime("%Y-%m")
            consumption_by_month[month_key] += delta

    rows: list[dict[str, str]] = []
    for month in sorted(grouped.keys()):
        month_readings = grouped[month]
        rows.append(
            {
                "month": month,
                "readings": str(len(month_readings)),
                "consumption": str(consumption_by_month[month]),
            }
        )
    return rows
