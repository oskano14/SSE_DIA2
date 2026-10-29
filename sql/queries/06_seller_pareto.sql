-- Question (Direction) : le chiffre d'affaires est-il concentré sur quelques
-- vendeurs (loi de Pareto) ?
-- Techniques : fonctions de fenêtre RANK et SUM cumulative.
WITH seller_revenue AS (
    SELECT i.seller_id, s.seller_state, sum(i.price) AS revenue
    FROM order_items AS i
    JOIN orders AS o USING (order_id)
    JOIN sellers AS s USING (seller_id)
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY i.seller_id, s.seller_state
)
SELECT
    rank() OVER (ORDER BY revenue DESC) AS seller_rank,
    seller_id,
    seller_state,
    round(revenue, 2) AS revenue,
    round(
        100 * sum(revenue) OVER (ORDER BY revenue DESC)
        / sum(revenue) OVER (), 1
    ) AS cumulative_share_pct
FROM seller_revenue
ORDER BY seller_rank
LIMIT 50;
