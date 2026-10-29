# Note de cadrage : ShopPulse Mission Flash

**Mission** : 10 jours, en tant que consultant data, pour le Directeur Data de ShopPulse.
**Livrables** : un dépôt GitHub exécutable et une soutenance vidéo de 10 minutes.

## 1. Contexte et enjeux métier

ShopPulse est une marketplace e-commerce. Elle compte environ 3 000 vendeurs et 96 000 clients,
pour 99 000 commandes entre 2016 et 2018 (données Olist). La direction exprime trois irritants :

| Irritant | Constat chiffré (état initial) | Enjeu |
|---|---|---|
| Données éparpillées | 9 fichiers CSV sans référentiel commun, des doublons (1 M de points GPS pour 19 000 codes postaux) et des dates incohérentes | Disposer d'une **source unique et fiable** |
| Marketing non ciblé | **97 % des clients n'achètent qu'une fois**, avec un taux de réachat de 3 % | Faire croître le CA **par la fidélisation** plutôt que par l'acquisition |
| Retards découverts trop tard | **6,8 % des livraisons sont en retard**, mais elles génèrent **32 % des avis négatifs** (note moyenne de 1,7/5 au-delà de 7 jours de retard) | **Anticiper** le retard au lieu de le subir |

## 2. Objectifs économiques

| Objectif | Indicateur | Cible | Levier livré |
|---|---|---|---|
| Doubler le réachat | Taux de clients avec 2 commandes ou plus | 3 % → 6 % | Segmentation RFM, 3 personas, 3 campagnes |
| CA additionnel | R$ générés par les campagnes | ≈ 490 k R$ (+3 % du CA), à valider par test A/B | Campagnes chiffrées (notebook 02) |
| Réduire les avis négatifs dus au retard | Part des notes de 1 ou 2 sur les commandes en retard | -20 % | API de risque de retard : action proactive sur le top 10 % des commandes |
| Traiter les plaintes plus vite | Délai de première réponse à un avis négatif | Avis négatifs traités en priorité | API de sentiment (94 % des avis négatifs détectés) |
| Piloter l'activité | Indicateurs consultés chaque semaine par la direction | 5 indicateurs à jour après chaque chargement | Tableau de bord Streamlit |

## 3. Utilisateurs et livrables

| Utilisateur | Question | Livrable | Forme |
|---|---|---|---|
| Direction | Comment se porte l'activité ? | Tableau de bord avec 5 indicateurs | Page web Streamlit |
| Marketing | Qui sont nos clients et comment les cibler ? | 3 personas et 3 actions chiffrées | Notebook commenté et README |
| Logistique | Quelle commande risque d'arriver en retard ? | Modèle de classification | Endpoint `POST /predict/delay` |
| Service client | Que disent les clients ? | Modèle de sentiment | Endpoint `POST /predict/sentiment` |
| Équipe data | Comment maintenir le tout ? | Pipeline rejouable, tests, CI, Docker | Dépôt GitHub |

## 4. Périmètre

- **Inclus** : PostgreSQL, ETL orchestré, 8 requêtes SQL, EDA et tests statistiques, RFM et clustering, tableau de bord, deux
  modèles et un audit d'équité, une API FastAPI conteneurisée, la CI GitHub Actions, une note éthique.
- **Exclus, en bonus éventuel** : Spark et le clickstream REES46, ELK, le déploiement AWS, MLflow.
- **Hypothèses** : les données Olist représentent ShopPulse, et la date de « maintenant » est le
  17/10/2018, date du dernier achat.

## 5. Planning et jalons

| Jours | Lot | Jalon de sortie |
|---|---|---|
| J1 | 1 · Cadrage | Note de cadrage, arbitrage, architecture, backlog |
| J2-J3 | 2 · Données fiables | Base chargée, rapport qualité, 8 requêtes SQL. **Point d'étape n°1** |
| J4-J5 | 3 · Analyse et marketing | EDA, tests, personas, tableau de bord |
| J6-J7 | 4 · Modèles | Modèle de retard, modèle de sentiment, audit d'équité, note éthique. **Point d'étape n°2** |
| J8-J9 | 5 · Industrialisation | API, Docker, CI au vert |
| J10 | Livraison | README final, rétrospective, vidéo |

**Risques principaux** :

1. Classes déséquilibrées pour le retard. **Parade** : métriques PR-AUC et rappel, pondération des classes.
2. Avis en portugais. **Parade** : entraînement direct sur le portugais, sans traduction.
3. Délai très court. **Parade** : on livre d'abord le minimum de chaque lot, les bonus ensuite.

## 6. Évolutions probables

- **Volumes** : passer de 100 000 à plus de 1 M de commandes par an, avec le clickstream REES46. Il faudrait alors Spark ou DuckDB
  pour les transformations, et des chargements incrémentaux plutôt qu'un rechargement complet.
- **Temps réel** : scorer le risque de retard **à la validation de la commande**, en appelant l'API depuis le back-office.
- **Cloud** : déployer l'API sur AWS (ECS Fargate ou App Runner), avec une base RDS PostgreSQL.
- **MLOps** :
  - suivre les expériences avec MLflow ;
  - ré-entraîner chaque mois, car une dérive a été mesurée ;
  - surveiller l'équité par région.
- **Sentiment par aspect** (produit, livraison, vendeur) pour les avis longs et mixtes.
