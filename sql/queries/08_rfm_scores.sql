-- Question (Marketing) : base de la segmentation RFM, avec pour chaque
-- client sa récence, sa fréquence, son montant et un score de 1 à 5.
-- Techniques : jointure multiple, agrégat, fonction de fenêtre NTILE.
-- La date de référence est le lendemain du dernier achat du jeu de données.
WITH reference AS (
    SELECT max(order_purchase_timestamp)::date + 1 AS ref_date FROM orders
),
customer_orders AS (
    SELECT
        c.customer_unique_id,
        max(o.order_purchase_timestamp) AS last_purchase,
        count(DISTINCT o.order_id) AS frequency,
        sum(p.payment_value) AS monetary
    FROM orders AS o
    JOIN customers AS c USING (customer_id)
    JOIN order_payments AS p USING (order_id)
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_unique_id
)
SELECT
    customer_unique_id,
    ref_date - last_purchase::date AS recency_days,
    frequency,
    round(monetary, 2) AS monetary,
    ntile(5) OVER (ORDER BY last_purchase) AS r_score,
    ntile(5) OVER (ORDER BY frequency, monetary) AS f_score,
    ntile(5) OVER (ORDER BY monetary) AS m_score
FROM customer_orders
CROSS JOIN reference
ORDER BY monetary DESC;
