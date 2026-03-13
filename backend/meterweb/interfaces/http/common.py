from fastapi import HTTPException, Request, status

TRANSLATIONS = {
    "de": {
        "login_error": "Ungültige Zugangsdaten.",
        "dashboard": "Dashboard",
    },
    "en": {
        "login_error": "Invalid credentials.",
        "dashboard": "Dashboard",
    },
}


def require_auth(request: Request) -> str:
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return username


def get_locale(request: Request) -> str:
    lang = request.query_params.get("lang") or request.session.get("lang") or "de"
    if lang not in TRANSLATIONS:
        lang = "de"
    request.session["lang"] = lang
    return lang
