import os

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from meterweb.infrastructure.db import configure_database, init_db
from meterweb.interfaces.http.router import router


def create_app() -> FastAPI:
    configure_database()

    app = FastAPI(title="meterweb")
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY", "dev-secret"),
        same_site="lax",
    )
    app.include_router(router)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    return app


app = create_app()
