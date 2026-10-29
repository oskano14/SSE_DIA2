# Construction depuis la racine du dépôt : docker build -f infra/Dockerfile .
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# Dépendances d'abord : couche mise en cache tant que uv.lock ne change pas.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-default-groups --no-install-project

COPY src ./src
COPY sql ./sql
COPY pipelines ./pipelines
COPY data/sample ./data/sample
RUN uv sync --frozen --no-default-groups

RUN useradd --create-home app && chown -R app /app
USER app

# Temporaire : l'API FastAPI (Lot 5) remplacera cette commande.
CMD ["python", "pipelines/etl_flow.py"]
