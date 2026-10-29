# ShopPulse : plateforme data & IA

Mission de 10 jours pour ShopPulse, une marketplace e-commerce. Les données
viennent du jeu public [Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce),
soit environ 100 000 commandes.

> En cours. Les lots 1 (cadrage), 3 (analyse), 4 (modèles) et 5 (API) restent à livrer.

## Démarrage rapide

Prérequis : [uv](https://docs.astral.sh/uv/), Docker et `make`.

```bash
make install   # dépendances + création de .env (à adapter)
make db        # PostgreSQL 16 dans Docker
make etl       # charge data/raw/ (ou data/sample/ si RAW_DIR=data/sample)
make test      # tests unitaires + tests de données
```

Les 9 CSV Olist sont à déposer dans `data/raw/`. Ce dossier n'est pas versionné.
Pour essayer sans télécharger le jeu complet, on peut utiliser l'échantillon
versionné : `RAW_DIR=data/sample make etl`.

## Données fiables (Lot 2)

| Livrable | Emplacement |
|---|---|
| Modèle relationnel (MLD) | [`docs/mld.md`](docs/mld.md), [`sql/schema.sql`](sql/schema.sql) |
| Pipeline ETL orchestré (Prefect) | [`pipelines/etl_flow.py`](pipelines/etl_flow.py) |
| Règles de nettoyage traçables | [`src/shoppulse/etl/clean.py`](src/shoppulse/etl/clean.py) |
| Rapport qualité avant/après (généré) | [`docs/quality_report.md`](docs/quality_report.md) |
| 8 requêtes d'analyse documentées | [`sql/README.md`](sql/README.md), [résultats](docs/sql_results.md) |

Le pipeline se déroule ainsi : **extraction → nettoyage → contrôles bloquants → chargement**.

- Les 9 tables sont décrites une seule fois, dans
  [`specs.py`](src/shoppulse/etl/specs.py) : clé primaire, dates, domaines de
  valeurs, clés étrangères. Toutes les étapes lisent cette description.
- Chaque règle de nettoyage est une petite fonction. Le nombre de lignes ou de
  cellules qu'elle modifie est consigné dans le rapport qualité.
- Les contrôles bloquants (clés nulles, clés dupliquées, valeurs hors domaine,
  orphelins) arrêtent le pipeline **avant** que la base ne soit modifiée.
- Le chargement est **idempotent** : tout se fait dans une seule transaction
  (`TRUNCATE` puis `COPY`). Une erreur laisse la base intacte, et deux exécutions
  donnent le même contenu. La CI lance d'ailleurs le pipeline deux fois.

## Qualité du code

- Le code est organisé en package `src/shoppulse`. Il est typé (`mypy --strict`)
  et vérifié par ruff, qui applique PEP 8 et l'ordre des imports.
- Les tests utilisent pytest, avec une couverture minimale de 50 % imposée par la CI.
  Les tests de données tournent sur la base chargée.
- La CI GitHub Actions comprend trois jobs : lint, tests sur une base PostgreSQL
  alimentée par l'échantillon, puis build de l'image Docker.

## Arborescence

```
data/sample/   échantillon (< 1 Mo par fichier), généré par make sample
docs/          MLD, rapport qualité, résultats SQL
infra/         Dockerfile, docker-compose
pipelines/     flows Prefect et scripts de génération
sql/           schéma et requêtes d'analyse
src/shoppulse/ package Python
tests/         tests unitaires et tests de données
```
