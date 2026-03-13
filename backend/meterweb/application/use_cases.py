import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from meterweb.application.dto import (
    AnalyticsViewDTO,
    BuildingCreateDTO,
    BuildingViewDTO,
    LoginDTO,
    MeterPointCreateDTO,
    MeterPointViewDTO,
    OCRCandidateDTO,
    OCRRunResultDTO,
    PhotoReadingCreateDTO,
    ReadingCreateDTO,
    ReadingViewDTO,
    UnitCreateDTO,
    UnitViewDTO,
)
from meterweb.application.ports import (
    Authenticator,
    BuildingRepository,
    MeterPointRepository,
    OCRProvider,
    ReadingRepository,
    ReportRenderer,
    UnitRepository,
    WeatherProvider,
    WeatherSeriesPoint,
    WeatherStationRepository,
)
from meterweb.domain.auth import Credentials, User
from meterweb.domain.building import Building, BuildingDomainService, BuildingName
from meterweb.domain.metering import (
    IntervalSample,
    MeterPoint,
    Unit,
    aggregate_intervals,
    consumption_from_absolute_readings,
    consumption_from_pulses,
    evaluate_plausibility,
)


@dataclass(frozen=True, slots=True)
class ReadingPlausibilityResult:
    plausible: bool
    warning: str | None


class LoginUseCase:
    def __init__(self, authenticator: Authenticator) -> None:
        self._authenticator = authenticator

    def execute(self, data: LoginDTO) -> User:
        return self._authenticator.authenticate(
            Credentials(username=data.username, password=data.password)
        )


class CreateBuildingUseCase:
    def __init__(self, repository: BuildingRepository) -> None:
        self._repository = repository

    def execute(self, data: BuildingCreateDTO) -> BuildingViewDTO:
        all_buildings = self._repository.list_all()
        names = {item.name.value.lower() for item in all_buildings}
        candidate_name = BuildingName(data.name)
        BuildingDomainService.ensure_name_is_unique(candidate_name, names)

        building = Building.create(candidate_name.value)
        self._repository.add(building)
        return BuildingViewDTO(id=building.id, name=building.name.value)


class ListBuildingsUseCase:
    def __init__(self, repository: BuildingRepository) -> None:
        self._repository = repository

    def execute(self) -> list[BuildingViewDTO]:
        return [
            BuildingViewDTO(id=item.id, name=item.name.value)
            for item in self._repository.list_all()
        ]


class CreateUnitUseCase:
    def __init__(self, repository: UnitRepository) -> None:
        self._repository = repository

    def execute(self, data: UnitCreateDTO) -> UnitViewDTO:
        unit = Unit(id=uuid4(), building_id=data.building_id, name=data.name.strip())
        if not unit.name:
            raise ValueError("Einheitsname darf nicht leer sein.")
        self._repository.add(unit)
        return UnitViewDTO(id=unit.id, building_id=unit.building_id, name=unit.name)


class ListUnitsUseCase:
    def __init__(self, repository: UnitRepository) -> None:
        self._repository = repository

    def execute(self) -> list[UnitViewDTO]:
        return [UnitViewDTO(id=i.id, building_id=i.building_id, name=i.name) for i in self._repository.list_all()]


class CreateMeterPointUseCase:
    def __init__(self, repository: MeterPointRepository) -> None:
        self._repository = repository

    def execute(self, data: MeterPointCreateDTO) -> MeterPointViewDTO:
        mp = MeterPoint(id=uuid4(), unit_id=data.unit_id, name=data.name.strip())
        if not mp.name:
            raise ValueError("Messpunktname darf nicht leer sein.")
        self._repository.add(mp)
        return MeterPointViewDTO(id=mp.id, unit_id=mp.unit_id, name=mp.name)


class ListMeterPointsUseCase:
    def __init__(self, repository: MeterPointRepository) -> None:
        self._repository = repository

    def execute(self) -> list[MeterPointViewDTO]:
        return [MeterPointViewDTO(id=i.id, unit_id=i.unit_id, name=i.name) for i in self._repository.list_all()]


class AddReadingUseCase:
    def __init__(self, repository: ReadingRepository) -> None:
        self._repository = repository

    def execute(self, data: ReadingCreateDTO) -> ReadingViewDTO:
        measured_at = data.measured_at
        if measured_at.tzinfo is None:
            measured_at = measured_at.replace(tzinfo=timezone.utc)
        created = self._repository.add_manual(data.meter_point_id, measured_at, data.value)
        plausibility = evaluate_reading_plausibility(self._repository, data.meter_point_id, ocr_confidence=None)
        return ReadingViewDTO(
            id=created.id,
            meter_point_id=data.meter_point_id,
            measured_at=created.measured_at,
            value=created.value,
            plausible=plausibility.plausible,
        )


class OCRRunUseCase:
    def __init__(self, provider: OCRProvider) -> None:
        self._provider = provider

    def execute(self, image_path: Path) -> OCRRunResultDTO:
        result = self._provider.extract_text(image_path)
        candidates: list[OCRCandidateDTO] = []
        best_score = (-1, -1, Decimal("-1"))
        best_candidate = None
        for token in re.findall(r"\d+(?:[\.,]\d+)?", result.text):
            normalized = token.replace(",", ".")
            try:
                candidate = OCRCandidateDTO(value=Decimal(normalized), confidence=result.confidence)
            except Exception:
                continue
            candidates.append(candidate)
            score = self._candidate_score(candidate)
            if score > best_score:
                best_score = score
                best_candidate = candidate
        return OCRRunResultDTO(text=result.text, candidates=candidates, best_candidate=best_candidate)

    @staticmethod
    def _candidate_score(candidate: OCRCandidateDTO) -> tuple[int, int, Decimal]:
        value = candidate.value
        is_integer = int(value == value.to_integral_value())
        digit_count = len(value.as_tuple().digits)
        return is_integer, digit_count, value


class AddPhotoReadingUseCase:
    def __init__(self, repository: ReadingRepository, ocr_use_case: OCRRunUseCase) -> None:
        self._repository = repository
        self._ocr_use_case = ocr_use_case

    def execute(self, data: PhotoReadingCreateDTO, confirmed_value: Decimal | None = None) -> tuple[ReadingViewDTO, OCRRunResultDTO, ReadingPlausibilityResult]:
        measured_at = data.measured_at
        if measured_at.tzinfo is None:
            measured_at = measured_at.replace(tzinfo=timezone.utc)
        ocr_result = self._ocr_use_case.execute(Path(data.image_path))
        value = confirmed_value if confirmed_value is not None else (ocr_result.best_candidate.value if ocr_result.best_candidate else None)
        if value is None:
            raise ValueError("Kein OCR-Kandidat erkannt. Bitte Wert manuell bestätigen.")
        ocr_confidence = ocr_result.best_candidate.confidence if ocr_result.best_candidate else 0.0
        created = self._repository.add_photo(data.meter_point_id, measured_at, value, data.image_path, ocr_confidence)
        plausibility = evaluate_reading_plausibility(self._repository, data.meter_point_id, ocr_confidence=ocr_confidence)
        return (
            ReadingViewDTO(
                id=created.id,
                meter_point_id=data.meter_point_id,
                measured_at=created.measured_at,
                value=created.value,
                plausible=plausibility.plausible,
            ),
            ocr_result,
            plausibility,
        )


class ExportUseCase:
    def __init__(self, reading_repository: ReadingRepository, report_renderer: ReportRenderer) -> None:
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
            rows.append({"month": month, "readings": str(len(month_readings)), "consumption": str(consumption)})
        return rows

    def export_csv(self, meter_point_id: UUID) -> bytes:
        return self._report_renderer.render_csv(self.monthly_rows(meter_point_id))

    def export_xlsx(self, meter_point_id: UUID) -> bytes:
        return self._report_renderer.render_xlsx(self.monthly_rows(meter_point_id))

    def export_pdf(self, meter_point_id: UUID) -> bytes:
        rows = self.monthly_rows(meter_point_id)
        html = "<h1>Monatsbericht</h1><table><tr><th>Monat</th><th>Ablesungen</th><th>Verbrauch</th></tr>"
        for row in rows:
            html += f"<tr><td>{row['month']}</td><td>{row['readings']}</td><td>{row['consumption']}</td></tr>"
        html += "</table>"
        return self._report_renderer.render_pdf(html)


class WeatherSyncUseCase:
    def __init__(self, weather_provider: WeatherProvider, station_repository: WeatherStationRepository) -> None:
        self._weather_provider = weather_provider
        self._station_repository = station_repository

    def select_station(self, building_id: UUID, latitude: float, longitude: float, force_auto: bool = False) -> str:
        override = None if force_auto else self._station_repository.get_override(building_id)
        station = override or self._weather_provider.find_station(latitude, longitude)
        return station

    def set_manual_station(self, building_id: UUID, station_id: str) -> None:
        self._station_repository.set_override(building_id, station_id)

    def set_auto_station(self, building_id: UUID) -> None:
        self._station_repository.set_override(building_id, None)

    def get_series(
        self,
        building_id: UUID,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        resolution: str,
    ) -> list[WeatherSeriesPoint]:
        station = self.select_station(building_id, latitude, longitude)
        return self._weather_provider.get_series(latitude, longitude, start_date, end_date, resolution, station_id=station)


def evaluate_reading_plausibility(repository: ReadingRepository, meter_point_id: UUID, ocr_confidence: float | None) -> ReadingPlausibilityResult:
    readings = repository.list_for_meter_point(meter_point_id)
    if len(readings) < 2:
        return ReadingPlausibilityResult(plausible=True, warning=None)
    previous = readings[-2]
    current = readings[-1]
    deltas = [
        next_reading.value - prev_reading.value
        for prev_reading, next_reading in zip(readings, readings[1:])
        if next_reading.value >= prev_reading.value
    ]
    plausibility = evaluate_plausibility(
        previous.value,
        current.value,
        historical_deltas=deltas[:-1] if deltas else [],
        max_expected_delta=Decimal("50000"),
        standstill_tolerance=Decimal("0.001"),
    )
    warning = None
    if ocr_confidence is not None and ocr_confidence < 0.55:
        warning = "OCR confidence is low"
    return ReadingPlausibilityResult(plausible=plausibility.is_plausible and warning is None, warning=warning)


class ProcessAbsoluteReadingUseCase:
    def compute_consumption(
        self,
        previous_value: Decimal,
        current_value: Decimal,
        rollover_limit: Decimal | None = None,
    ) -> Decimal:
        return consumption_from_absolute_readings(previous_value, current_value, rollover_limit)


class ProcessPulseReadingUseCase:
    def compute_consumption(self, pulse_delta: int, pulse_factor: Decimal) -> Decimal:
        return consumption_from_pulses(pulse_delta, pulse_factor)


class ProcessIntervalReadingUseCase:
    def compute_consumption(
        self,
        meter_register_id: UUID,
        period_start: datetime,
        period_end: datetime,
        interval_values: list[tuple[datetime, datetime, Decimal]],
    ) -> Decimal:
        aggregate = aggregate_intervals(
            meter_register_id=meter_register_id,
            period_start=period_start,
            period_end=period_end,
            samples=[
                IntervalSample(start_at=start_at, end_at=end_at, value=value)
                for start_at, end_at, value in interval_values
            ],
        )
        return aggregate.consumption


class RecomputeAggregatesUseCase:
    def __init__(self, repository: ReadingRepository) -> None:
        self._repository = repository

    def execute(self, meter_point_id: UUID, price_per_unit: Decimal) -> AnalyticsViewDTO:
        analytics = AnalyticsUseCase(self._repository)
        return analytics.execute(meter_point_id, price_per_unit)


class AnalyticsUseCase:
    def __init__(self, repository: ReadingRepository) -> None:
        self._repository = repository

    def execute(self, meter_point_id: UUID, price_per_unit: Decimal) -> AnalyticsViewDTO:
        readings = self._repository.list_for_meter_point(meter_point_id)
        consumption = Decimal("0")
        for prev, current in zip(readings, readings[1:]):
            try:
                consumption += consumption_from_absolute_readings(prev.value, current.value)
            except ValueError:
                continue
        return AnalyticsViewDTO(
            meter_point_id=meter_point_id,
            consumption=consumption,
            cost=consumption * price_per_unit,
        )
