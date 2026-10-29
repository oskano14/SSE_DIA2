-- Question (Logistique) : dans quels États les livraisons sont-elles le plus
-- souvent en retard, et combien de jours faut-il pour livrer ?
-- Techniques : vue partagée, agrégat avec FILTER, HAVING pour écarter les
-- États trop peu représentés.
SELECT
    customer_state,
    count(*) AS delivered_orders,
    round(100.0 * count(*) FILTER (WHERE is_late) / count(*), 1) AS late_rate_pct,
    round(avg(delivery_days), 1) AS avg_delivery_days
FROM delivered_orders
GROUP BY customer_state
HAVING count(*) >= 30
ORDER BY late_rate_pct DESC;
