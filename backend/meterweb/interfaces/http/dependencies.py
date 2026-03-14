from functools import lru_cache
from fastapi import Depends
from sqlalchemy.orm import Session

from meterweb.application.use_cases.analytics import AnalyticsUseCase
from meterweb.application.use_cases.auth import LoginUseCase
from meterweb.application.use_cases.buildings import (
    CreateBuildingUseCase,
    CreateMeterPointWithDefaultDeviceUseCase,
    CreateUnitUseCase,
    ListBuildingsUseCase,
    ListMeterPointsUseCase,
    ListUnitsUseCase,
)
from meterweb.application.use_cases.exports import ExportUseCase
from meterweb.application.use_cases.readings import (
    AddPhotoReadingUseCase,
    AddReadingUseCase,
    ConfirmReadingUseCase,
    CorrectReadingUseCase,
    OCRAcceptUseCase,
    OCRRejectUseCase,
    OCRRunUseCase,
)
from meterweb.application.use_cases.weather import WeatherSyncUseCase
from meterweb.bootstrap import AppContainer, get_container
from meterweb.infrastructure.db import get_session
from meterweb.infrastructure.settings import AppSettings
from meterweb.interfaces.http.web.auth_security import LoginAttemptGuard


def container() -> AppContainer:
    return get_container()


def get_app_settings(app_container: AppContainer = Depends(container)) -> AppSettings:
    return app_container.settings


def get_login_use_case(app_container: AppContainer = Depends(container)) -> LoginUseCase:
    return app_container.login_use_case()


@lru_cache
def get_login_attempt_guard() -> LoginAttemptGuard:
    settings = container().settings
    return LoginAttemptGuard(
        max_attempts=settings.login_max_attempts,
        window_seconds=settings.login_attempt_window_seconds,
        lock_duration_seconds=settings.login_lock_duration_seconds,
    )


def get_create_building_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> CreateBuildingUseCase:
    return app_container.create_building_use_case(session)


def get_list_buildings_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> ListBuildingsUseCase:
    return app_container.list_buildings_use_case(session)


def get_create_unit_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> CreateUnitUseCase:
    return app_container.create_unit_use_case(session)


def get_list_units_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> ListUnitsUseCase:
    return app_container.list_units_use_case(session)


def get_create_meter_point_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> CreateMeterPointWithDefaultDeviceUseCase:
    return app_container.create_meter_point_with_default_device_use_case(session)


def get_list_meter_points_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> ListMeterPointsUseCase:
    return app_container.list_meter_points_use_case(session)


def get_add_reading_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> AddReadingUseCase:
    return app_container.add_reading_use_case(session)


def get_ocr_run_use_case(app_container: AppContainer = Depends(container)) -> OCRRunUseCase:
    return app_container.ocr_run_use_case()


def get_add_photo_reading_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> AddPhotoReadingUseCase:
    return app_container.add_photo_reading_use_case(session)


def get_export_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> ExportUseCase:
    return app_container.export_use_case(session)


def get_weather_sync_use_case(app_container: AppContainer = Depends(container)) -> WeatherSyncUseCase:
    return app_container.weather_sync_use_case()


def get_analytics_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> AnalyticsUseCase:
    return app_container.analytics_use_case(session)


def get_confirm_reading_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> ConfirmReadingUseCase:
    return app_container.confirm_reading_use_case(session)


def get_correct_reading_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> CorrectReadingUseCase:
    return app_container.correct_reading_use_case(session)


def get_ocr_accept_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> OCRAcceptUseCase:
    return app_container.ocr_accept_use_case(session)


def get_ocr_reject_use_case(
    session: Session = Depends(get_session),
    app_container: AppContainer = Depends(container),
) -> OCRRejectUseCase:
    return app_container.ocr_reject_use_case(session)
