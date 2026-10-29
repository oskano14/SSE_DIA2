-- Les 5 indicateurs clés du tableau de bord Direction (une seule ligne).
-- Mêmes définitions que les requêtes d'analyse : CA hors annulations, retard
-- issu de la vue delivered_orders.
WITH sales AS (
    SELECT
        sum(i.price + i.freight_value) AS revenue,
        count(DISTINCT o.order_id) AS orders
    FROM orders AS o
    JOIN order_items AS i USING (order_id)
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
),
delivery AS (
    SELECT avg(is_late::int) AS late_rate FROM delivered_orders
),
satisfaction AS (
    SELECT avg(review_score) AS avg_score FROM order_reviews
)
SELECT
    round(revenue, 2) AS revenue,
    orders,
    round(revenue / orders, 2) AS avg_basket,
    round(100 * late_rate, 1) AS late_rate_pct,
    round(avg_score, 2) AS avg_review_score
FROM sales, delivery, satisfaction;
