import logging

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse

from meterweb.application.dto import LoginDTO
from meterweb.application.use_cases.auth import LoginUseCase
from meterweb.domain.auth import AuthenticationError
from meterweb.interfaces.http.common import enforce_csrf, TRANSLATIONS, get_locale
from meterweb.interfaces.http.dependencies import get_login_attempt_guard, get_login_use_case
from meterweb.interfaces.http.web.auth_security import LoginAttemptGuard
from meterweb.interfaces.http.templating import create_templates

templates = create_templates()
router = APIRouter(tags=["web-auth"])
logger = logging.getLogger("meterweb.auth")


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_page(request: Request):
    lang = get_locale(request)
    return templates.TemplateResponse(request, "login.html", {"error": None, "lang": lang})


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    client = request.client
    return client.host if client else "unknown"


@router.post("/login", dependencies=[Depends(enforce_csrf)])
def login_submit(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    use_case: LoginUseCase = Depends(get_login_use_case),
    login_guard: LoginAttemptGuard = Depends(get_login_attempt_guard),
):
    lang = get_locale(request)
    ip_address = _client_ip(request)
    keys = (f"ip:{ip_address}", f"account:{username.strip().lower()}")

    if any(login_guard.is_locked(key) for key in keys):
        logger.warning("login_locked ip=%s username=%s", ip_address, username)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": TRANSLATIONS[lang]["login_error"], "lang": lang},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    try:
        use_case.execute(LoginDTO(username=username, password=password))
    except AuthenticationError:
        for key in keys:
            login_guard.register_failure(key)
        logger.warning("login_failed ip=%s username=%s", ip_address, username)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": TRANSLATIONS[lang]["login_error"], "lang": lang},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    for key in keys:
        login_guard.register_success(key)
    logger.info("login_success ip=%s username=%s", ip_address, username)
    request.session["username"] = username
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
