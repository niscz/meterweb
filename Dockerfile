# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libxml2 \
        libxslt1.1 \
        tesseract-ocr \
        tesseract-ocr-deu \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./pyproject.toml
COPY backend/meterweb ./meterweb

RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels .[ocr,reports]


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_DATA_DIR=/data \
    UPLOADS_DIR=/uploads \
    REPORTS_DIR=/reports \
    BACKUPS_DIR=/backups

WORKDIR /app

RUN adduser --disabled-password --gecos '' appuser

COPY --from=builder /wheels /wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libxml2 \
        libxslt1.1 \
        tesseract-ocr \
        tesseract-ocr-deu \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

RUN mkdir -p /data /uploads /reports /backups && chown -R appuser:appuser /data /uploads /reports /backups

USER appuser

EXPOSE 8000

CMD ["uvicorn", "meterweb.main:app", "--host", "0.0.0.0", "--port", "8000"]
