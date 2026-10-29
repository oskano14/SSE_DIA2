COMPOSE = docker compose -f infra/docker-compose.yml

.PHONY: install db etl train sample sql-report notebooks dashboard api api-dev lint test docker down

install:  ## Dépendances Python + fichier .env local
	uv sync
	test -f .env || cp .env.example .env

db:  ## Démarre PostgreSQL
	$(COMPOSE) up -d --wait db

etl:  ## Pipeline complet : CSV -> contrôles -> PostgreSQL + rapport qualité
	uv run python pipelines/etl_flow.py

train:  ## Entraîne les modèles servis par l'API (base chargée) -> models/
	uv run python pipelines/train.py

sample:  ## Régénère data/sample/ depuis data/raw/
	uv run python pipelines/make_sample.py

sql-report:  ## Exécute les 8 requêtes et écrit docs/sql_results.md
	uv run python pipelines/sql_report.py

notebooks:  ## Réexécute les notebooks d'analyse (base chargée)
	uv run jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb

dashboard:  ## Tableau de bord Direction sur http://localhost:8501
	uv run streamlit run dashboards/app.py

api:  ## API conteneurisée sur http://localhost:8000/docs (après make train)
	$(COMPOSE) up -d --build --wait api

api-dev:  ## API locale avec rechargement automatique
	uv run uvicorn shoppulse.api:app --reload

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
