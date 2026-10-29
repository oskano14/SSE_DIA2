-- Schéma physique ShopPulse (données Olist). Idempotent : rejouable sans erreur.
-- Le MLD commenté est dans docs/mld.md.

CREATE TABLE IF NOT EXISTS category_translation (
    product_category_name          TEXT PRIMARY KEY,
    product_category_name_english  TEXT NOT NULL
);

-- Un point GPS médian par préfixe de code postal (agrégé par le pipeline).
-- Pas de clé étrangère depuis clients/vendeurs : certains préfixes n'ont
-- pas de coordonnées dans la source, on garde quand même ces lignes.
CREATE TABLE IF NOT EXISTS geolocation (
    geolocation_zip_code_prefix  TEXT PRIMARY KEY,
    geolocation_lat              DOUBLE PRECISION NOT NULL,
    geolocation_lng              DOUBLE PRECISION NOT NULL,
    geolocation_city             TEXT,
    geolocation_state            CHAR(2)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id               TEXT PRIMARY KEY,
    customer_unique_id        TEXT NOT NULL,
    customer_zip_code_prefix  TEXT,
    customer_city             TEXT,
    customer_state            CHAR(2)
);

CREATE TABLE IF NOT EXISTS sellers (
    seller_id               TEXT PRIMARY KEY,
    seller_zip_code_prefix  TEXT,
    seller_city             TEXT,
    seller_state            CHAR(2)
);

CREATE TABLE IF NOT EXISTS products (
    product_id                  TEXT PRIMARY KEY,
    product_category_name       TEXT
        REFERENCES category_translation (product_category_name),
    product_name_length         INTEGER,
    product_description_length  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            INTEGER,
    product_length_cm           INTEGER,
    product_height_cm           INTEGER,
    product_width_cm            INTEGER
);

CREATE TABLE IF NOT EXISTS orders (
    order_id                       TEXT PRIMARY KEY,
    customer_id                    TEXT NOT NULL REFERENCES customers (customer_id),
    order_status                   TEXT NOT NULL,
    order_purchase_timestamp       TIMESTAMP NOT NULL,
    order_approved_at              TIMESTAMP,
    order_delivered_carrier_date   TIMESTAMP,
    order_delivered_customer_date  TIMESTAMP,
    order_estimated_delivery_date  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id             TEXT NOT NULL REFERENCES orders (order_id),
    order_item_id        INTEGER NOT NULL,
    product_id           TEXT NOT NULL REFERENCES products (product_id),
    seller_id            TEXT NOT NULL REFERENCES sellers (seller_id),
    shipping_limit_date  TIMESTAMP,
    price                NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    freight_value        NUMERIC(10, 2) NOT NULL CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS order_payments (
    order_id              TEXT NOT NULL REFERENCES orders (order_id),
    payment_sequential    INTEGER NOT NULL,
    payment_type          TEXT NOT NULL,
    payment_installments  INTEGER NOT NULL CHECK (payment_installments >= 0),
    payment_value         NUMERIC(10, 2) NOT NULL CHECK (payment_value >= 0),
    PRIMARY KEY (order_id, payment_sequential)
);

-- review_id n'est pas unique dans la source : clé composite.
CREATE TABLE IF NOT EXISTS order_reviews (
    review_id                TEXT NOT NULL,
    order_id                 TEXT NOT NULL REFERENCES orders (order_id),
    review_score             SMALLINT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title     TEXT,
    review_comment_message   TEXT,
    review_creation_date     TIMESTAMP,
    review_answer_timestamp  TIMESTAMP,
    PRIMARY KEY (review_id, order_id)
);

-- Index sur les clés étrangères les plus utilisées par les analyses.
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_items_product ON order_items (product_id);
CREATE INDEX IF NOT EXISTS idx_items_seller ON order_items (seller_id);
CREATE INDEX IF NOT EXISTS idx_reviews_order ON order_reviews (order_id);

-- Vue partagée par les requêtes d'analyse, le tableau de bord et le modèle de
-- retard : une seule définition du « retard ».
-- Une commande est en retard si elle est livrée un jour calendaire après la
-- date estimée (la date estimée est fournie à minuit, sans heure).
CREATE OR REPLACE VIEW delivered_orders AS
SELECT
    o.order_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_purchase_timestamp,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    o.order_delivered_customer_date::date
        - o.order_purchase_timestamp::date AS delivery_days,
    o.order_delivered_customer_date::date
        > o.order_estimated_delivery_date::date AS is_late
FROM orders AS o
JOIN customers AS c USING (customer_id)
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL;
