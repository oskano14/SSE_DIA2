-- Question (Marketing) : quelle part des clients revient acheter ?
-- Techniques : sous-requête d'agrégat par personne (customer_unique_id),
-- puis agrégat global.
WITH orders_per_person AS (
    SELECT c.customer_unique_id, count(DISTINCT o.order_id) AS orders
    FROM orders AS o
    JOIN customers AS c USING (customer_id)
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_unique_id
)
SELECT
    count(*) AS customers,
    count(*) FILTER (WHERE orders > 1) AS repeat_customers,
    round(100.0 * count(*) FILTER (WHERE orders > 1) / count(*), 2)
        AS repeat_rate_pct,
    round(avg(orders), 3) AS avg_orders_per_customer
FROM orders_per_person;
