# Rétrospective

## Écarts avec la feuille de route

| Prévu (note de cadrage) | Réalisé | Écart et cause |
|---|---|---|
| Lot 1 à J1, avant le code | Cadrage formalisé **après** les lots 2 à 5 | Le socle technique a été lancé dès réception des données, pour sécuriser la partie exécutable. Le cadrage a été rédigé ensuite, à partir de chiffres réels plutôt que d'hypothèses. C'est un écart de méthode assumé (voir « ce que je referais »). |
| Commits quotidiens sur 10 jours | Historique concentré sur peu de jours | Le travail a avancé par lots complets. Une branche par lot et des commits conventionnels ont été respectés, mais pas le rythme quotidien. |
| 5 lots minimum | 5 lots livrés, CI au vert | Aucun bonus réalisé (Spark, ELK, AWS, MLflow), conformément à la règle « socle d'abord ». |
| Modèle de retard validé en validation croisée | Validation croisée **et** validation temporelle | Ajout non prévu : la validation temporelle révèle une **dérive** (PR-AUC de 0,23 en validation croisée, 0,16 sur une période future). C'est la limite la plus importante à communiquer. |
| Réseau de neurones de sentiment | Livré, mais **non servi** | Il est à égalité avec la baseline TF-IDF pour 27 fois plus de temps d'entraînement. On sert la baseline, plus légère et plus explicable. |

## Ce qui a bien fonctionné

- **Une description unique des tables** ([`specs.py`](../src/shoppulse/etl/specs.py)). Ajouter une règle ou une table ne demande qu'une ligne, et le rapport qualité est généré automatiquement.
- **Des contrôles bloquants avant le chargement, et un chargement transactionnel**. Aucune base à moitié chargée n'est possible, et l'idempotence est prouvée en CI, qui lance l'ETL deux fois.
- **Un échantillon cohérent versionné** (moins de 1 Mo par fichier). Il permet une CI réaliste, de l'ETL jusqu'au test de fumée de l'API, sans les données complètes.
- **Des features partagées entre l'entraînement et l'API**. Il n'y a pas d'écart entre ce que le modèle a appris et ce qu'il reçoit en production.

## Difficultés rencontrées et corrections

| Problème | Correction |
|---|---|
| Le million de points GPS dupliqués faisait 10 Mo dans l'échantillon | Agrégation au point médian par préfixe postal. L'échantillon est limité à 5 points par code postal. |
| Le conteneur de l'API plantait (`pyarrow` manquant pour désérialiser les tables pandas) | `pyarrow` ajouté aux dépendances principales. Le test de fumée en CI détecte désormais ce type d'erreur. |
| L'image Docker pesait 3,2 Go | Cache de uv désactivé et `chown -R` supprimé, ce qui la ramène à 1,3 Go. |
| Le seuil de 0,5 alertait sur 30 % des commandes, ce qui est inexploitable | Le modèle sert de classement par risque : on alerte sur les 10 % les plus risquées, qui captent 37 % des retards. |

## Ce que je referais autrement

1. **Rédiger le cadrage et ouvrir le backlog (GitHub Projects) au J1**, puis tenir les points d'étape au fil de l'eau plutôt qu'en fin de lot.
2. **Commiter chaque jour en petites unités**, même incomplètes, sur la branche du lot.
3. **Valider le modèle dans le temps dès le départ.** La dérive aurait orienté plus tôt le choix des features vers les conditions de transport.
4. **Séparer les dépendances de l'API de celles du pipeline**, sans Prefect ni SQLAlchemy dans l'image servie, pour viser une image de moins de 500 Mo.
5. **Tracer les expériences avec MLflow** au lieu de comparer les résultats dans les notebooks.
