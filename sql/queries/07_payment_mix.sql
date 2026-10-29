-- Question (Finance) : comment les clients paient-ils, et en combien de
-- mensualités ?
-- Techniques : agrégat, part du total par fonction de fenêtre.
SELECT
    payment_type,
    count(*) AS payments,
    round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS share_pct,
    round(avg(payment_value), 2) AS avg_value,
    round(avg(payment_installments), 1) AS avg_installments
FROM order_payments
GROUP BY payment_type
ORDER BY payments DESC;
