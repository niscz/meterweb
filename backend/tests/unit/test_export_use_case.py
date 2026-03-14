from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from meterweb.application.use_cases.exports import ExportUseCase
from meterweb.domain.metering import Reading


class FakeReadingRepository:
    def __init__(self, readings: list[Reading]):
        self._readings = readings

    def list_for_meter_register(self, register_id):
        return [r for r in self._readings if r.meter_register_id == register_id]

    def list_for_meter_point(self, _meter_point_id):
        return self._readings

    def list_for_building(self, _building_id):
        return self._readings


class FakeReportRenderer:
    def __init__(self):
        self.last_pdf_context = None

    def render_csv(self, _rows):
        return b"csv"

    def render_xlsx(self, _rows):
        return b"xlsx"

    def render_pdf_template(self, _template, _context):
        self.last_pdf_context = _context
        return b"pdf"


def test_monthly_rows_group_deltas_by_register_for_interleaved_readings() -> None:
    ht = uuid4()
    nt = uuid4()
    readings = [
        Reading(id=uuid4(), meter_register_id=ht, measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc), value=Decimal("100")),
        Reading(id=uuid4(), meter_register_id=nt, measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc), value=Decimal("50")),
        Reading(id=uuid4(), meter_register_id=ht, measured_at=datetime(2025, 1, 15, tzinfo=timezone.utc), value=Decimal("110")),
        Reading(id=uuid4(), meter_register_id=nt, measured_at=datetime(2025, 1, 15, tzinfo=timezone.utc), value=Decimal("58")),
    ]

    use_case = ExportUseCase(FakeReadingRepository(readings), FakeReportRenderer())
    rows = use_case.monthly_rows_for_meter_point(uuid4())

    assert rows == [{"month": "2025-01", "readings": "4", "consumption": "18"}]


def test_export_pdf_passes_selected_language_to_renderer() -> None:
    register_id = uuid4()
    readings = [
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc), value=Decimal("100")),
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 1, 2, tzinfo=timezone.utc), value=Decimal("101")),
    ]
    renderer = FakeReportRenderer()
    use_case = ExportUseCase(FakeReadingRepository(readings), renderer)

    payload = use_case.export_pdf(uuid4(), lang="en")

    assert payload == b"pdf"
    assert renderer.last_pdf_context is not None
    assert renderer.last_pdf_context["lang"] == "en"
