-- Question (Direction) : comment évoluent le chiffre d'affaires et le volume
-- de commandes mois par mois ?
-- Techniques : agrégat, fonction de fenêtre LAG pour la croissance mensuelle.
-- CA = prix des articles + frais de port, hors commandes annulées/indisponibles.
WITH monthly AS (
    SELECT
        date_trunc('month', o.order_purchase_timestamp)::date AS month,
        count(DISTINCT o.order_id) AS orders,
        sum(i.price + i.freight_value) AS revenue
    FROM orders AS o
    JOIN order_items AS i USING (order_id)
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY 1
)
SELECT
    month,
    orders,
    round(revenue, 2) AS revenue,
    round(
        100 * (revenue / lag(revenue) OVER (ORDER BY month) - 1), 1
    ) AS revenue_growth_pct
FROM monthly
ORDER BY month;
