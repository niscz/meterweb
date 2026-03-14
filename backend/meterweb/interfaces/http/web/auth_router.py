from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse

from meterweb.application.dto import LoginDTO
from meterweb.application.use_cases.auth import LoginUseCase
from meterweb.domain.auth import AuthenticationError
from meterweb.interfaces.http.common import enforce_csrf, TRANSLATIONS, get_locale
from meterweb.interfaces.http.dependencies import get_login_use_case
from meterweb.interfaces.http.templating import create_templates

templates = create_templates()
router = APIRouter(tags=["web-auth"])


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_page(request: Request):
    lang = get_locale(request)
    return templates.TemplateResponse(request, "login.html", {"error": None, "lang": lang})


@router.post("/login", dependencies=[Depends(enforce_csrf)])
def login_submit(request: Request, username: str = Form(), password: str = Form(), use_case: LoginUseCase = Depends(get_login_use_case)):
    lang = get_locale(request)
    try:
        use_case.execute(LoginDTO(username=username, password=password))
    except AuthenticationError:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": TRANSLATIONS[lang]["login_error"], "lang": lang},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    request.session["username"] = username
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
