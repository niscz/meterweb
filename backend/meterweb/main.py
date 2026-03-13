import os

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from meterweb.infrastructure.auth import validate_runtime_security_config
from meterweb.infrastructure.db import configure_database, init_db
from meterweb.interfaces.http.errors import register_exception_handlers
from meterweb.interfaces.http.router import router


def create_app() -> FastAPI:
    configure_database()

    secret_key = validate_runtime_security_config()

    app = FastAPI(title="meterweb")

    session_options = {
        "secret_key": secret_key,
        "same_site": "strict",
        "https_only": True,
        "max_age": int(os.getenv("SESSION_MAX_AGE", "3600")),
        "path": os.getenv("SESSION_COOKIE_PATH", "/"),
    }
    session_domain = os.getenv("SESSION_COOKIE_DOMAIN")
    if session_domain:
        session_options["domain"] = session_domain

    app.add_middleware(SessionMiddleware, **session_options)
    register_exception_handlers(app)
    app.include_router(router)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    return app


app = create_app()
