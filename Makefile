COMPOSE = docker compose -f infra/docker-compose.yml

.PHONY: install db etl sample sql-report notebooks dashboard lint test docker down

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

notebooks:  ## Réexécute les notebooks d'analyse (base chargée)
	uv run jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb

dashboard:  ## Tableau de bord Direction sur http://localhost:8501
	uv run streamlit run dashboards/app.py

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
