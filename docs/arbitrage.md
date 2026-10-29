# Arbitrages techniques

## 1. Orchestration : Prefect 3 contre Apache Airflow

**Besoin** : un ETL rejouable (extraction, contrôles qualité, chargement idempotent) et un entraînement
des modèles. Le volume est d'environ 100 000 commandes, le tout est lancé à la demande ou une fois par jour, par une seule personne, en 10 jours.

| Critère | Prefect 3 | Apache Airflow | Avantage |
|---|---|---|---|
| **Coût** | Open source. Les flows sont du Python ordinaire, et un serveur local éphémère démarre tout seul. Aucune infrastructure n'est nécessaire en développement. | Open source, mais il faut un ordonnanceur, un serveur web, une base de métadonnées et des workers, soit au moins 4 conteneurs et environ 4 Go de RAM recommandés. Un service managé (MWAA, Astronomer) coûte au moins 300 $ par mois. | **Prefect** |
| **Délai de mise en place** | Il suffit d'ajouter des décorateurs `@flow` et `@task` sur des fonctions existantes. Le premier flow tourne en quelques minutes, et un tiers peut le lancer avec `python pipelines/etl_flow.py`. | Il faut écrire des DAGs, déployer le docker-compose officiel et gérer les connexions et les variables. Comptez environ une journée pour un premier DAG fiable. | **Prefect** |
| **Performance** | Les tâches s'exécutent dans le processus, et les DataFrames passent en mémoire. L'ETL complet prend environ 40 s. Les reprises sont configurées par tâche (`retries=2` sur le chargement). | Le passage de données entre tâches passe par XCom (limité) ou par un stockage intermédiaire. Le temps d'ordonnancement est d'environ une seconde par tâche. Airflow est très robuste à grande échelle. | **Prefect** à cette échelle, **Airflow** au-delà |
| **Pérennité** | Plus jeune (2018) et porté par une entreprise. L'API a cassé entre les versions 1, 2 et 3, ce qui est un risque de migration. | Standard du marché, projet Apache depuis 2016, très grande communauté, nombreux connecteurs. C'est aussi le profil le plus recherché en recrutement. | **Airflow** |

**Décision : Prefect.** Il gagne sur le coût, le délai et la performance à notre échelle. Ce sont les critères
décisifs pour une mission de 10 jours, avec un dépôt qu'un tiers doit pouvoir exécuter en moins de 30 minutes.

**Maîtrise du risque de pérennité** : toute la logique vit dans le package `shoppulse.etl`, sous forme de fonctions
pures testées sans Prefect. Les flows ([`etl_flow.py`](../pipelines/etl_flow.py), [`train.py`](../pipelines/train.py))
ne font qu'environ 60 lignes d'assemblage. Migrer vers Airflow reviendrait donc à réécrire ces deux fichiers en DAG, et
c'est ce que nous recommandons si les volumes ou le nombre de pipelines sont multipliés par dix (voir les évolutions dans la note de cadrage).

## 2. Tableau de bord : Streamlit contre Metabase

| Critère | Streamlit | Metabase | Avantage |
|---|---|---|---|
| **Coût** | Gratuit, une dépendance Python de plus | Gratuit en version open source, mais il faut un conteneur Java et sa propre base applicative | Streamlit |
| **Délai** | Environ 60 lignes de Python. Les requêtes SQL du projet sont **réutilisées telles quelles**. | Construction à la souris, rapide, mais la configuration est stockée dans Metabase : elle n'est ni versionnée ni testée. | Streamlit |
| **Performance** | Mise en cache des requêtes pendant 10 minutes, largement suffisant pour quelques utilisateurs | Très bon, avec un cache intégré et des droits par utilisateur | Égalité |
| **Pérennité et autonomie** | Le code est versionné et passe en revue de code, mais il faut un développeur pour le faire évoluer. | Les utilisateurs métier sont **autonomes** pour créer leurs propres questions. | Metabase |

**Décision : Streamlit**, car il est versionné, testable et sans service supplémentaire. Si la direction veut
créer ses propres analyses, Metabase est l'évolution naturelle : il se branche sur la même base PostgreSQL, sans
autre changement.

## 3. Autres choix structurants

| Sujet | Choix | Alternative écartée | Raison |
|---|---|---|---|
| Base | PostgreSQL 16 (Docker) | DuckDB, SQLite | Le sujet l'impose. Contraintes d'intégrité (clés étrangères, CHECK), multi-utilisateur. |
| Sentiment | Entraînement direct sur le portugais (TF-IDF + régression logistique) | Traduction, BERT multilingue | Même performance que le réseau de neurones, une image légère, pas d'envoi des avis à un tiers (RGPD). Détails dans le notebook 04. |
| Modèle de retard | Gradient boosting (scikit-learn) | XGBoost, LightGBM | Performance équivalente attendue, sans dépendance supplémentaire, et valeurs manquantes gérées nativement. |
| Paquets Python | uv | pip, Poetry | Installation reproductible (`uv.lock`) et très rapide, ce qui aide pour le délai de 30 minutes. |
