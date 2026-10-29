# Rapport qualité (généré par le pipeline, ne pas éditer)

Source : `data/raw`

## Indicateurs avant / après nettoyage

| table | lignes avant | lignes après | clés dupliquées avant | hors domaine avant | orphelins avant | taux de NULL avant | taux de NULL après |
|---|---|---|---|---|---|---|---|
| category_translation | 71 | 71 | 0 | 0 | 0 | 0.0 | 0.0 |
| geolocation | 1000163 | 19010 | 981148 | 0 | 0 | 0.0 | 0.0 |
| customers | 99441 | 99441 | 0 | 0 | 0 | 0.0 | 0.0 |
| sellers | 3095 | 3095 | 0 | 0 | 0 | 0.0 | 0.0 |
| products | 32951 | 32951 | 0 | 0 | 13 | 0.0083 | 0.0083 |
| orders | 99441 | 99441 | 0 | 0 | 0 | 0.0062 | 0.0064 |
| order_items | 112650 | 112650 | 0 | 0 | 0 | 0.0 | 0.0 |
| order_payments | 103886 | 103886 | 0 | 0 | 0 | 0.0 | 0.0 |
| order_reviews | 99224 | 99224 | 0 | 0 | 0 | 0.2101 | 0.2101 |

Après nettoyage, tous les contrôles bloquants valent 0 : clés nulles, clés dupliquées, valeurs hors domaine, orphelins.

## Journal des règles appliquées (règles ayant eu un effet)

| table | rule | description | affected |
|---|---|---|---|
| geolocation | strip_strings | Supprime les espaces superflus et remplace les textes vides par NULL. | 1 |
| geolocation | normalize_cities | Normalise les noms de ville : minuscules et sans accents. | 73442 |
| geolocation | drop_outside_brazil | Supprime les coordonnées GPS situées hors du Brésil. | 42 |
| geolocation | aggregate_by_zip | Agrège les points GPS en un point médian par préfixe de code postal. | 981111 |
| sellers | normalize_cities | Normalise les noms de ville : minuscules et sans accents. | 3 |
| products | orphan_product_category_name | product_category_name absent de category_translation : vide la référence. | 13 |
| orders | null_impossible_dates | Vide les dates d'étape antérieures à la date d'achat. | 166 |
| order_reviews | strip_strings | Supprime les espaces superflus et remplace les textes vides par NULL. | 11449 |
