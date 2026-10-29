-- Question (Marketing) : quelles catégories de produits génèrent le plus de
-- chiffre d'affaires, et avec quel panier moyen ?
-- Techniques : jointure multiple (4 tables), agrégat, LEFT JOIN pour garder
-- les produits sans catégorie.
SELECT
    coalesce(t.product_category_name_english, 'unknown') AS category,
    count(DISTINCT i.order_id) AS orders,
    round(sum(i.price), 2) AS revenue,
    round(avg(i.price), 2) AS avg_item_price
FROM order_items AS i
JOIN orders AS o USING (order_id)
JOIN products AS p USING (product_id)
LEFT JOIN category_translation AS t USING (product_category_name)
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY 1
ORDER BY revenue DESC
LIMIT 10;
