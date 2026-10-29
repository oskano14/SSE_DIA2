# SQL

- [`schema.sql`](schema.sql) : tables, contraintes, index et la vue `delivered_orders`,
  qui est la seule définition du retard dans le projet. Le pipeline l'applique à chaque exécution.
- [`queries/`](queries/) : les 8 requêtes d'analyse. Chaque fichier commence par la question
  métier à laquelle il répond et par les techniques SQL qu'il utilise.

| # | Requête | Destinataire | Techniques |
|---|---|---|---|
| 1 | [CA mensuel et croissance](queries/01_monthly_revenue.sql) | Direction | agrégat, fenêtre `LAG` |
| 2 | [Top 10 catégories](queries/02_top_categories.sql) | Marketing | jointure de 4 tables, `LEFT JOIN` |
| 3 | [Taux de retard par État](queries/03_late_rate_by_state.sql) | Logistique | vue, `FILTER`, `HAVING` |
| 4 | [Note selon le retard](queries/04_review_score_vs_delay.sql) | Service client | jointure, `CASE` |
| 5 | [Taux de réachat](queries/05_repeat_purchase_rate.sql) | Marketing | CTE, agrégat par personne |
| 6 | [Concentration des vendeurs](queries/06_seller_pareto.sql) | Direction | fenêtres `RANK`, `SUM` cumulée |
| 7 | [Moyens de paiement](queries/07_payment_mix.sql) | Finance | part du total par fenêtre |
| 8 | [Scores RFM](queries/08_rfm_scores.sql) | Marketing | jointure multiple, `NTILE` |

Les résultats sont dans [`docs/sql_results.md`](../docs/sql_results.md), générés par `make sql-report`.
