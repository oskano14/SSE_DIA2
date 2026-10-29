# Modèle logique de données (MLD)

Le schéma physique est dans [`sql/schema.sql`](../sql/schema.sql). Il est créé
et rechargé par le pipeline ([`pipelines/etl_flow.py`](../pipelines/etl_flow.py)).

```mermaid
erDiagram
    customers ||--o{ orders : passe
    orders ||--|{ order_items : contient
    orders ||--o{ order_payments : "est réglée par"
    orders ||--o{ order_reviews : "reçoit"
    products ||--o{ order_items : "est vendu dans"
    sellers ||--o{ order_items : expédie
    category_translation ||--o{ products : classe
    geolocation |o..o{ customers : "localise (zip)"
    geolocation |o..o{ sellers : "localise (zip)"

    customers {
        text customer_id PK
        text customer_unique_id "identifiant de la personne"
        text customer_zip_code_prefix
        text customer_city
        char customer_state
    }
    orders {
        text order_id PK
        text customer_id FK
        text order_status
        timestamp order_purchase_timestamp
        timestamp order_approved_at
        timestamp order_delivered_carrier_date
        timestamp order_delivered_customer_date
        timestamp order_estimated_delivery_date
    }
    order_items {
        text order_id PK, FK
        int order_item_id PK
        text product_id FK
        text seller_id FK
        timestamp shipping_limit_date
        numeric price
        numeric freight_value
    }
    order_payments {
        text order_id PK, FK
        int payment_sequential PK
        text payment_type
        int payment_installments
        numeric payment_value
    }
    order_reviews {
        text review_id PK
        text order_id PK, FK
        smallint review_score
        text review_comment_title
        text review_comment_message
        timestamp review_creation_date
        timestamp review_answer_timestamp
    }
    products {
        text product_id PK
        text product_category_name FK
        int product_weight_g
        int product_length_cm
        int product_height_cm
        int product_width_cm
    }
    sellers {
        text seller_id PK
        text seller_zip_code_prefix
        text seller_city
        char seller_state
    }
    category_translation {
        text product_category_name PK
        text product_category_name_english
    }
    geolocation {
        text geolocation_zip_code_prefix PK
        float geolocation_lat
        float geolocation_lng
        text geolocation_city
        char geolocation_state
    }
```

## Choix de modélisation

| Choix | Justification |
|---|---|
| `customer_id` est la clé de `customers`, et `customer_unique_id` reste un attribut | Olist crée un `customer_id` à chaque commande. La personne réelle est `customer_unique_id`, et c'est la clé à utiliser pour le RFM et le réachat. |
| Clé composite `(review_id, order_id)` | `review_id` n'est pas unique dans la source : un même avis peut porter sur plusieurs commandes. |
| `geolocation` est agrégée à un point par préfixe postal | La source contient environ 1 M de points, avec beaucoup de doublons pour un même préfixe. On garde la médiane, qui résiste aux points aberrants. |
| Pas de clé étrangère entre le code postal et `geolocation` | Certains préfixes de clients ou de vendeurs n'ont pas de coordonnées. Imposer la contrainte ferait perdre des clients réels. On fait donc une jointure externe (`LEFT JOIN`). |
| La catégorie inconnue d'un produit devient NULL | Deux catégories (13 produits) n'existent pas dans la table de traduction. On garde le produit et on vide seulement sa référence. Cette règle est tracée dans le rapport qualité. |
| Colonnes `*_lenght` renommées en `*_length` | La faute de frappe vient de la source et est corrigée à l'extraction. |
