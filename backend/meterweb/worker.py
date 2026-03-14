"""Basic worker entrypoint for scheduled/background jobs."""

import logging
import os
import time
from datetime import date, timedelta
from uuid import UUID

from meterweb.bootstrap import get_container
from meterweb.infrastructure.db import configure_database, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _sync_weather() -> None:
    building_id = os.getenv("WEATHER_BUILDING_ID")
    lat = os.getenv("WEATHER_LAT")
    lon = os.getenv("WEATHER_LON")
    if not building_id or not lat or not lon:
        logger.info("Weather sync skipped: WEATHER_BUILDING_ID/WEATHER_LAT/WEATHER_LON not set")
        return
    use_case = get_container().weather_sync_use_case()
    today = date.today()
    start = today - timedelta(days=2)
    use_case.get_series(UUID(building_id), float(lat), float(lon), start, today, "hourly")
    use_case.get_series(UUID(building_id), float(lat), float(lon), start, today, "daily")
    logger.info("Weather sync completed for building %s", building_id)


def main() -> None:
    configure_database()
    init_db()
    logger.info("Worker started. Waiting for jobs.")
    while True:
        _sync_weather()
        time.sleep(60)


if __name__ == "__main__":
    main()
