-- Jeu d'apprentissage du modèle de retard : une ligne par commande livrée.
-- Uniquement des informations connues au moment de l'achat (pas de fuite) :
-- les dates de livraison réelles ne servent qu'à la cible is_late.
-- Vendeur principal = vendeur de l'article le plus cher de la commande.
WITH items AS (
    SELECT
        i.order_id,
        (array_agg(i.seller_id ORDER BY i.price DESC))[1] AS seller_id,
        count(*) AS n_items,
        sum(i.price) AS total_price,
        sum(i.freight_value) AS total_freight,
        sum(p.product_weight_g) AS total_weight_g,
        sum(p.product_length_cm * p.product_height_cm * p.product_width_cm)
            AS total_volume_cm3
    FROM order_items AS i
    JOIN products AS p USING (product_id)
    GROUP BY i.order_id
)
SELECT
    d.order_id,
    d.order_purchase_timestamp,
    d.order_estimated_delivery_date,
    d.customer_state,
    s.seller_state,
    it.seller_id,
    gc.geolocation_lat AS customer_lat,
    gc.geolocation_lng AS customer_lng,
    gs.geolocation_lat AS seller_lat,
    gs.geolocation_lng AS seller_lng,
    it.n_items,
    it.total_price,
    it.total_freight,
    it.total_weight_g,
    it.total_volume_cm3,
    d.is_late
FROM delivered_orders AS d
JOIN orders AS o USING (order_id)
JOIN customers AS c USING (customer_id)
JOIN items AS it USING (order_id)
JOIN sellers AS s USING (seller_id)
LEFT JOIN geolocation AS gc
    ON gc.geolocation_zip_code_prefix = c.customer_zip_code_prefix
LEFT JOIN geolocation AS gs
    ON gs.geolocation_zip_code_prefix = s.seller_zip_code_prefix
ORDER BY d.order_purchase_timestamp;
