-- Question (Service client) : un retard de livraison dégrade-t-il la note
-- laissée par le client ?
-- Techniques : jointure, agrégat, CASE pour construire des tranches de retard.
SELECT
    CASE
        WHEN NOT d.is_late THEN '0. à l''heure'
        WHEN d.order_delivered_customer_date::date
            - d.order_estimated_delivery_date::date <= 3 THEN '1. 1-3 jours'
        WHEN d.order_delivered_customer_date::date
            - d.order_estimated_delivery_date::date <= 7 THEN '2. 4-7 jours'
        ELSE '3. plus de 7 jours'
    END AS delay_bucket,
    count(*) AS reviews,
    round(avg(r.review_score), 2) AS avg_score,
    round(100.0 * count(*) FILTER (WHERE r.review_score <= 2) / count(*), 1)
        AS negative_rate_pct
FROM delivered_orders AS d
JOIN order_reviews AS r USING (order_id)
GROUP BY 1
ORDER BY 1;
