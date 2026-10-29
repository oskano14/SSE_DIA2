COMPOSE = docker compose -f infra/docker-compose.yml

.PHONY: install db etl sample sql-report lint test docker down

install:  ## Dépendances Python + fichier .env local
	uv sync
	test -f .env || cp .env.example .env

db:  ## Démarre PostgreSQL
	$(COMPOSE) up -d --wait

etl:  ## Pipeline complet : CSV -> contrôles -> PostgreSQL + rapport qualité
	uv run python pipelines/etl_flow.py

sample:  ## Régénère data/sample/ depuis data/raw/
	uv run python pipelines/make_sample.py

sql-report:  ## Exécute les 8 requêtes et écrit docs/sql_results.md
	uv run python pipelines/sql_report.py

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

test:
	uv run pytest

docker:
	docker build -f infra/Dockerfile -t shoppulse .

down:
	$(COMPOSE) down
