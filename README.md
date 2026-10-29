# ShopPulse : plateforme data & IA

**Le problème.** ShopPulse est une marketplace d'environ 3 000 vendeurs et 96 000 clients. Ses données
sont éparpillées, et son marketing cible tout le monde alors que **97 % des clients n'achètent qu'une fois**.
Ses retards de livraison (6,8 % des commandes) génèrent **32 % des avis négatifs**, que l'entreprise
découvre après coup.

**Ce que la plateforme apporte**, en 10 jours, sur les données réelles
[Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (environ 100 000 commandes) :

| Pour | Réponse | Résultat clé |
|---|---|---|
| Direction | Tableau de bord, 5 indicateurs | 15,7 M R$ de CA, 6,8 % de retards, note de 4,1/5 |
| Marketing | 3 personas, 3 campagnes chiffrées | ≈ 490 k R$ de CA additionnel, réachat de 3 % à 6 % |
| Logistique | API de risque de retard | Le top 10 % des commandes à risque contient 37 % des retards |
| Service client | API de sentiment des avis | 94 % des avis négatifs détectés |

## Architecture

```mermaid
flowchart LR
    subgraph Sources
        CSV[(9 CSV Olist<br/>data/raw)]
    end

    subgraph Orchestration["Orchestration Prefect"]
        ETL["etl_flow<br/>extraction → nettoyage →<br/>contrôles bloquants → COPY"]
        TRAIN["train_flow<br/>gradient boosting retard<br/>TF-IDF sentiment"]
    end

    subgraph Stockage
        PG[("PostgreSQL 16<br/>9 tables + vue delivered_orders")]
        QR["docs/quality_report.md"]
        ART["models/*.joblib"]
    end

    subgraph Consommation
        NB["Notebooks<br/>EDA · RFM · modèles"]
        DASH["Streamlit<br/>5 indicateurs (Direction)"]
        API["FastAPI dans Docker<br/>/predict/delay · /predict/sentiment"]
    end

    subgraph Utilisateurs
        DIR([Direction])
        MKT([Marketing])
        LOG([Logistique])
        SAV([Service client])
    end

    CSV --> ETL --> PG
    ETL --> QR
    PG --> TRAIN --> ART --> API
    PG --> NB --> MKT
    PG --> DASH --> DIR
    API --> LOG
    API --> SAV

    subgraph CI["GitHub Actions (à chaque push ou PR)"]
        direction TB
        L[ruff + mypy] --> T["ETL ×2 sur l'échantillon<br/>pytest ≥ 50 %"] --> B["entraînement → docker build<br/>→ test de fumée de l'API"]
    end
```

Les choix sont justifiés dans [`docs/arbitrage.md`](docs/arbitrage.md) (Prefect contre Airflow, Streamlit contre Metabase).
Les principes de l'architecture sont dans [`docs/architecture.md`](docs/architecture.md).

## Documentation

| Document | Contenu |
|---|---|
| [Note de cadrage](docs/cadrage.md) | Enjeux, objectifs économiques, utilisateurs, planning, évolutions |
| [Arbitrages techniques](docs/arbitrage.md) | Coût, délai, performance, pérennité |
| [Architecture](docs/architecture.md) | Schéma cible et principes |
| [MLD](docs/mld.md) | Modèle relationnel et choix de modélisation |
| [Rapport qualité](docs/quality_report.md) | Avant/après, généré par le pipeline |
| [Note éthique](docs/ethique.md) | Biais par région, RGPD, limites d'usage |
| [Rétrospective](docs/retro.md) | Écarts avec la feuille de route, ce que je referais |

## Démarrage rapide

Prérequis : [uv](https://docs.astral.sh/uv/), Docker et `make`.

```bash
git clone https://github.com/oskano14/SSE_DIA2.git && cd SSE_DIA2
```

```bash
make install   # dépendances + création de .env (à adapter)
make db        # PostgreSQL 16 dans Docker
make etl       # charge data/raw/ (ou data/sample/ si RAW_DIR=data/sample)
make train     # entraîne les modèles -> models/
make api       # API conteneurisée : http://localhost:8000/docs
make test      # tests unitaires + tests de données + tests API
make dashboard # tableau de bord Direction sur http://localhost:8501
```

Comptez environ 10 minutes sur le jeu complet, dont environ 1 min pour l'ETL et 1 min pour l'entraînement.

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

## Analyse et marketing (Lot 3)

| Livrable | Emplacement |
|---|---|
| EDA : distributions, saisonnalité, géographie | [`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb) |
| 2 tests statistiques motivés | même notebook, sections 5 et 6 |
| Segmentation RFM + K-means, 3 personas, 3 actions chiffrées | [`notebooks/02_segmentation.ipynb`](notebooks/02_segmentation.ipynb) |
| Tableau de bord, 5 indicateurs, branché sur la base | [`dashboards/app.py`](dashboards/app.py) |

### Réponses métier

- **Comment se porte l'activité ? (Direction)** Le chiffre d'affaires est de 15,7 M R$ sur environ
  98 000 commandes, avec un panier moyen de 160 R$. 6,8 % des livraisons arrivent en retard, et la
  note moyenne est de 4,1/5.
- **Que disent les clients ? (Service client)** Le retard fait chuter la note : 4,3/5 pour une
  commande à l'heure, 1,7/5 au-delà de 7 jours de retard. Un test de Mann-Whitney le confirme
  (p ≈ 0, effet fort, r = 0,64).
- **Où sont les retards ? (Logistique)** Le Nordeste subit 2 fois plus de retards que le Sud
  (12,7 % contre 5,9 %). Un χ² confirme le lien avec la région (p ≈ 10⁻¹²⁰).
- **Qui sont nos clients ? (Marketing)** 97 % des clients n'achètent qu'une fois. On distingue
  3 personas :

  | Persona | Clients | Action | Gain estimé |
  |---|---|---|---|
  | Récents | 35 % | -10 % sur un 2e achat, 30 jours après la livraison | ≈ 260 k R$ |
  | Endormis | 62 % | Réactivation à -15 % pendant 15 jours | ≈ 154 k R$ |
  | Fidèles | 3 % | Club fidélité avec livraison offerte | ≈ 73 k R$ |

  Ces trois actions rapporteraient environ 490 k R$, et le taux de réachat passerait de 3 % à 6 %.
  Les hypothèses de conversion restent à valider par un test A/B.

![Tableau de bord Direction](dashboards/dashboard.jpg)

## Modèles (Lot 4)

| Livrable | Emplacement |
|---|---|
| Feature engineering justifié | [`features.py`](src/shoppulse/features.py), [notebook 03](notebooks/03_delay_model.ipynb), section 1 |
| Retard : baseline et 2 algorithmes, validation croisée, importance | [`notebooks/03_delay_model.ipynb`](notebooks/03_delay_model.ipynb) |
| Audit d'équité par région | notebook 03, section 6, [`fairness.py`](src/shoppulse/fairness.py) |
| Sentiment : TF-IDF + régression logistique contre un réseau PyTorch | [`notebooks/04_sentiment.ipynb`](notebooks/04_sentiment.ipynb) |
| Note éthique | [`docs/ethique.md`](docs/ethique.md) |

### Retard de livraison (Logistique)

Le modèle classe les commandes par risque. Il a été comparé sur 96 000 commandes, en validation croisée
stratifiée à 5 plis.

| Modèle | PR-AUC | ROC-AUC |
|---|---|---|
| Baseline (taux moyen) | 0,07 | 0,50 |
| Régression logistique | 0,15 | 0,69 |
| **Gradient boosting** | **0,23** | **0,77** |

- **Usage** : en contrôlant les **10 % de commandes les plus risquées**, la logistique intercepte **37 %
  des retards**.
- **Variables clés** : l'historique du vendeur, la distance et le délai promis.
- **Équité** : le Nordeste reçoit 2,8 fois plus de fausses alertes. Le modèle ne doit servir qu'à
  des actions **protectrices** pour le client (voir la [note éthique](docs/ethique.md)).

### Sentiment des avis (Service client)

On entraîne directement sur le portugais, avec 39 000 avis. Les notes de 4-5 et de 1-2 servent d'étiquettes.

| Modèle | F1 macro | Rappel des négatifs | Entraînement |
|---|---|---|---|
| **TF-IDF + régression logistique** (servi) | **0,927** | 94 % | 0,6 s |
| Réseau PyTorch (embeddings + MLP) | 0,923 | 95 % | 17 s |

Les deux modèles sont à égalité. On sert la baseline, qui est plus légère et plus explicable. Les plaintes
portent d'abord sur la livraison : « não recebi », « não chegou », « demora ».

## API conteneurisée (Lot 5)

L'API FastAPI ([`api.py`](src/shoppulse/api.py)) expose un endpoint par modèle. Les entrées sont
validées par Pydantic, et la documentation OpenAPI interactive est disponible sur `/docs`.

| Endpoint | Rôle |
|---|---|
| `GET /health` | État du service et métriques des modèles chargés |
| `POST /predict/delay` | Probabilité de retard d'une commande et alerte « risque élevé » (top 10 %) |
| `POST /predict/sentiment` | Sentiment d'un avis en portugais |

```bash
curl -X POST localhost:8000/predict/delay -H 'content-type: application/json' -d '{
  "customer_zip_code_prefix": "69005", "seller_id": "6560211a19b47992c3666cc44a7e94c0",
  "purchase_timestamp": "2018-03-10T14:30:00", "estimated_delivery_date": "2018-03-20",
  "n_items": 1, "total_price": 129.9, "total_freight": 40, "total_weight_g": 800}'
# {"late_probability":0.881,"high_risk":true,"threshold":0.6976}

curl -X POST localhost:8000/predict/sentiment -H 'content-type: application/json' \
  -d '{"text": "Não recebi o produto, péssimo"}'
# {"sentiment":"negative","positive_probability":0.0002}
```

- **Fonctionnement autonome** : les modèles sont produits par [`pipelines/train.py`](pipelines/train.py), un flow Prefect,
  puis copiés dans l'image. L'API ne dépend donc pas de la base : les correspondances vendeur et code postal sont
  embarquées dans l'artefact.
- **Erreurs** : une entrée invalide renvoie **422** (code postal sur 5 chiffres, montants positifs, date estimée
  postérieure à l'achat). Un vendeur ou un code postal inconnu renvoie **404**.
- **Image** : elle tourne sous un utilisateur non root et dispose d'un `HEALTHCHECK`. La CI entraîne les modèles sur
  l'échantillon, construit l'image, lance le conteneur et l'interroge (test de fumée).

## Qualité du code

- Le code est organisé en package `src/shoppulse`. Il est typé (`mypy --strict`)
  et vérifié par ruff, qui applique PEP 8 et l'ordre des imports.
- Les tests utilisent pytest, avec une couverture minimale de 50 % imposée par la CI.
  Les tests de données tournent sur la base chargée.
- La CI GitHub Actions comprend deux jobs :
  - **lint** : ruff et mypy ;
  - **test** : ETL lancé deux fois sur l'échantillon, puis pytest, entraînement, build
    de l'image et test de fumée du conteneur.

## Arborescence

```
dashboards/    tableau de bord Streamlit et capture
data/sample/   échantillon (< 1 Mo par fichier), généré par make sample
docs/          cadrage, arbitrage, architecture, MLD, qualité, éthique, rétro
infra/         Dockerfile, docker-compose
notebooks/     EDA, tests statistiques, segmentation, modèles
pipelines/     flows Prefect et scripts de génération
sql/           schéma et requêtes d'analyse
src/shoppulse/ package Python
tests/         tests unitaires, tests de données et tests de l'API
```

## Auteur

Dorian ([@oskano14](https://github.com/oskano14)). Projet individuel, seconde session DIA2 2025-2026.

## Usage de l'IA

J'ai utilisé l'assistant **Claude Code** (Anthropic) comme binôme de programmation tout au long du projet.

- **Ce que l'IA a fait** : proposer une structure, écrire une première version du code, des tests et des
  notebooks, rédiger les brouillons de la documentation, et diagnostiquer des erreurs (dépendance manquante dans
  Docker, taille de l'image).
- **Ce que j'ai décidé et vérifié** :
  - les principes de code (KISS, PEP 8, DRY) et la stack (Prefect, Streamlit) ;
  - la relecture et la validation de chaque lot ;
  - les commits et l'intégration par pull request.
- **Garde-fous** :
  - chaque chiffre cité vient d'une exécution réelle du pipeline ou des notebooks sur la base chargée, et aucun résultat n'est saisi à la main ;
  - le code est contrôlé par ruff, mypy, 73 tests et la CI ;
  - les traitements s'exécutent en local. Pendant le développement, l'assistant n'a vu que des extraits
    (agrégats, quelques avis d'exemple). Le jeu Olist est public et pseudonymisé, mais sur des données
    clients réelles, ce mode de travail devrait être validé par le DPO.
