from fastapi import FastAPI, Request, status
from sqlalchemy.exc import IntegrityError
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from meterweb.application.errors import UpstreamServiceError
from meterweb.domain.auth import AuthenticationError
from meterweb.domain.metering import MeteringDomainError


def _json_error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(_: Request, exc: AuthenticationError) -> JSONResponse:
        return _json_error(status.HTTP_401_UNAUTHORIZED, str(exc) or "Authentication failed.")

    @app.exception_handler(MeteringDomainError)
    async def metering_domain_error_handler(_: Request, exc: MeteringDomainError) -> JSONResponse:
        return _json_error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))

    @app.exception_handler(UpstreamServiceError)
    async def upstream_service_error_handler(_: Request, exc: UpstreamServiceError) -> JSONResponse:
        return _json_error(status.HTTP_502_BAD_GATEWAY, str(exc) or "Upstream service unavailable.")

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_: Request, __: IntegrityError) -> JSONResponse:
        return _json_error(status.HTTP_409_CONFLICT, "Datenintegrität verletzt.")

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
        return _json_error(status.HTTP_400_BAD_REQUEST, str(exc))

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})
