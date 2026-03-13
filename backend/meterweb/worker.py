"""Basic worker entrypoint for scheduled/background jobs."""

import logging
import time

from meterweb.infrastructure.db import configure_database, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    configure_database()
    init_db()
    logger.info("Worker started. Waiting for jobs.")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
