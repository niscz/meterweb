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

Login standardmäßig: `admin` / `admin` (per `ADMIN_USERNAME` / `ADMIN_PASSWORD` überschreibbar).
