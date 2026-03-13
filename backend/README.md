# meterweb Backend (Basisstruktur)

Diese Basis implementiert einen modularen Monolithen mit klaren Schichten:

- `meterweb/domain`: Entities, Value Objects, Domain Services
- `meterweb/application`: Use Cases und DTOs
- `meterweb/infrastructure`: SQLAlchemy + Adapter/Provider
- `meterweb/interfaces/http`: FastAPI Router + HTTP-Modelle
- `meterweb/templates`: Jinja2 + Tabler UI
- `tests/unit` und `tests/integration`

## Starten

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn meterweb.main:app --reload
```

## Sicherheitsrelevante Pflicht-Konfiguration

Die Anwendung startet nur, wenn folgende Umgebungsvariablen gesetzt und stark genug sind:

- `SECRET_KEY` (mindestens 32 Zeichen sowie Klein-/Großbuchstabe, Zahl, Sonderzeichen; keine Platzhalterwerte)
- `ADMIN_USERNAME` (mindestens 3 Zeichen; kein Standardwert wie `admin`; keine Platzhalterwerte)
- `ADMIN_PASSWORD` (mindestens 12 Zeichen sowie Klein-/Großbuchstabe, Zahl, Sonderzeichen; keine Platzhalterwerte)

Zusätzliche optionale Session-Konfiguration:

- `SESSION_MAX_AGE` (Standard: `3600` Sekunden)
- `SESSION_COOKIE_PATH` (Standard: `/`)
- `SESSION_COOKIE_DOMAIN` (optional, für produktive Domains)

Session-Cookies werden mit sicheren Defaults gesetzt (`https_only=True`, `same_site="strict"`, `max_age` gesetzt). In Produktion muss TLS/HTTPS erzwungen sein, da Secure-Cookies sonst vom Browser nicht gesendet werden.

## First-Run / Bootstrap-Admin

Beim ersten Start wird aus `ADMIN_PASSWORD` ein PBKDF2-Hash erzeugt und in `ADMIN_PASSWORD_HASH_FILE` gespeichert (Standard: `.meterweb_admin_password.hash`). Es gibt **keinen** hardcodierten Standardzugang.

- Existiert die Hash-Datei bereits, muss `ADMIN_PASSWORD` weiterhin gesetzt sein und zum gespeicherten Hash passen.
- Für einen kontrollierten Reset kann die Hash-Datei gelöscht und der Dienst mit neuem `ADMIN_PASSWORD` erneut gestartet werden.
