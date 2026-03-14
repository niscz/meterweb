import secrets

from fastapi import HTTPException, Request, status

TRANSLATIONS = {
    "de": {
        "login_error": "Ungültige Zugangsdaten.",
        "login_title": "Anmeldung | meterweb",
        "login_header": "meterweb Anmeldung",
        "language_de": "DE",
        "language_en": "EN",
        "username": "Benutzername",
        "password": "Passwort",
        "sign_in": "Anmelden",
        "dashboard_title": "Dashboard | meterweb",
        "dashboard_heading": "Stammdaten & Erfassung",
        "building": "Gebäude",
        "create": "Anlegen",
        "unit": "Einheit",
        "meter_point": "Messpunkt",
        "monthly_report": "Monatsbericht",
        "manual_reading": "Manuelle Ablesung",
        "save": "Speichern",
        "photo_ocr_capture": "Foto/OCR-Erfassung",
        "optional_override": "Optionaler Override",
        "upload_ocr": "Upload + OCR",
        "consumption": "Verbrauch",
        "cost": "Kosten",
        "kwh": "kWh",
        "eur": "€",
        "capture_confirm_title": "OCR-Bestätigung | meterweb",
        "capture_confirm_heading": "OCR-Bestätigung",
        "recognized_text": "Erkannter Text",
        "best_candidate": "Bester Kandidat",
        "confidence": "Konfidenz",
        "stored_reading": "Gespeicherter Stand",
        "back": "Zurück",
        "buildings_title": "Gebäude | meterweb",
        "buildings_heading": "Gebäude",
        "new_building_placeholder": "Neues Gebäude",
        "create_building": "Gebäude anlegen",
        "no_buildings": "Noch keine Gebäude vorhanden.",
        "monthly_report_title": "Monatsbericht | meterweb",
        "monthly_report_heading": "Monatsbericht je Objekt",
        "month": "Monat",
        "readings": "Ablesungen",
        "reading_not_plausible": "Ablesung ist unplausibel",
        "photo_reading_invalid_input": "Die Foto-Ablesung enthält ungültige Eingaben. Bitte prüfen Sie Datum und Zählerstand.",
        "photo_reading_ocr_failed": "Die OCR-Verarbeitung ist fehlgeschlagen. Bitte Foto erneut aufnehmen oder Wert manuell eingeben.",
        "photo_reading_failed": "Die Foto-Ablesung konnte nicht gespeichert werden. Bitte erneut versuchen.",
    },
    "en": {
        "login_error": "Invalid credentials.",
        "login_title": "Login | meterweb",
        "login_header": "meterweb Login",
        "language_de": "DE",
        "language_en": "EN",
        "username": "Username",
        "password": "Password",
        "sign_in": "Sign in",
        "dashboard_title": "Dashboard | meterweb",
        "dashboard_heading": "Master data & capture",
        "building": "Building",
        "create": "Create",
        "unit": "Unit",
        "meter_point": "Meter point",
        "monthly_report": "Monthly report",
        "manual_reading": "Manual reading",
        "save": "Save",
        "photo_ocr_capture": "Photo/OCR capture",
        "optional_override": "Optional override",
        "upload_ocr": "Upload + OCR",
        "consumption": "Consumption",
        "cost": "Cost",
        "kwh": "kWh",
        "eur": "€",
        "capture_confirm_title": "OCR confirmation | meterweb",
        "capture_confirm_heading": "OCR confirmation",
        "recognized_text": "Recognized text",
        "best_candidate": "Best candidate",
        "confidence": "Confidence",
        "stored_reading": "Stored reading",
        "back": "Back",
        "buildings_title": "Buildings | meterweb",
        "buildings_heading": "Buildings",
        "new_building_placeholder": "New building",
        "create_building": "Create building",
        "no_buildings": "No buildings available yet.",
        "monthly_report_title": "Monthly report | meterweb",
        "monthly_report_heading": "Monthly report by object",
        "month": "Month",
        "readings": "Readings",
        "reading_not_plausible": "Reading is not plausible",
        "photo_reading_invalid_input": "The photo reading contains invalid input. Please verify date and meter value.",
        "photo_reading_ocr_failed": "OCR processing failed. Please retake the photo or enter the value manually.",
        "photo_reading_failed": "The photo reading could not be saved. Please try again.",
    },
}

CSRF_SESSION_KEY = "csrf_token"
CSRF_FORM_FIELD = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"


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


def translate(lang: str, key: str) -> str:
    locale = lang if lang in TRANSLATIONS else "de"
    fallback = TRANSLATIONS["de"]
    return TRANSLATIONS[locale].get(key, fallback.get(key, key))


def get_csrf_token(request: Request) -> str:
    token = request.session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[CSRF_SESSION_KEY] = token
    return token


async def enforce_csrf(request: Request) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
        get_csrf_token(request)
        return

    if request.url.path.startswith("/api/v1") and not request.session.get("username"):
        return

    session_token = get_csrf_token(request)
    submitted_token = request.headers.get(CSRF_HEADER)

    if not submitted_token:
        content_type = request.headers.get("content-type", "").lower()
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form_data = await request.form()
            submitted_token = form_data.get(CSRF_FORM_FIELD)

    if not submitted_token or not secrets.compare_digest(session_token, str(submitted_token)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
