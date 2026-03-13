"""Startup bootstrap for containerized execution."""

from meterweb.infrastructure.db import configure_database, init_db


def main() -> None:
    configure_database()
    init_db()


if __name__ == "__main__":
    main()
