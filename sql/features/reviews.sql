-- Jeu d'apprentissage du modèle de sentiment : avis avec un texte.
-- Titre et message sont concaténés ; la région sert à l'analyse d'erreurs.
SELECT
    r.review_id,
    r.review_score,
    concat_ws(' ', r.review_comment_title, r.review_comment_message) AS text,
    c.customer_state
FROM order_reviews AS r
JOIN orders AS o USING (order_id)
JOIN customers AS c USING (customer_id)
WHERE r.review_comment_message IS NOT NULL
   OR r.review_comment_title IS NOT NULL;
