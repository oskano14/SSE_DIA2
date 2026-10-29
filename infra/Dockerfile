# Image de l'API. Pré-requis : modèles entraînés dans models/ (make train).
# Construction depuis la racine du dépôt : docker build -f infra/Dockerfile .
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv
# UV_NO_CACHE : le cache de téléchargement ne doit pas rester dans l'image.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_CACHE=1 \
    PATH="/app/.venv/bin:$PATH"

# Utilisateur non root, propriétaire de /app dès le départ (évite un chown -R
# qui dupliquerait toute la couche des dépendances).
RUN useradd --create-home app && mkdir /app && chown app /app
USER app
WORKDIR /app

# Dépendances d'abord : couche mise en cache tant que uv.lock ne change pas.
COPY --chown=app pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-default-groups --no-install-project

COPY --chown=app src ./src
COPY --chown=app sql ./sql
COPY --chown=app pipelines ./pipelines
COPY --chown=app data/sample ./data/sample
COPY --chown=app models ./models
RUN uv sync --frozen --no-default-groups

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
CMD ["uvicorn", "shoppulse.api:app", "--host", "0.0.0.0", "--port", "8000"]
