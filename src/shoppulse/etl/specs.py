"""Description déclarative des 9 tables Olist : source unique pour l'ETL.

L'ordre de TABLES respecte les dépendances (tables parentes d'abord).
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ForeignKey:
    column: str
    parent: str
    parent_column: str
    # "drop" supprime la ligne orpheline, "null" vide seulement la référence.
    on_orphan: str = "drop"


@dataclass(frozen=True)
class TableSpec:
    name: str
    file: str
    primary_key: tuple[str, ...]
    dates: tuple[str, ...] = ()
    strings: tuple[str, ...] = ()
    cities: tuple[str, ...] = ()
    ranges: dict[str, tuple[float | None, float | None]] = field(default_factory=dict)
    foreign_keys: tuple[ForeignKey, ...] = ()
    renames: dict[str, str] = field(default_factory=dict)


TABLES: tuple[TableSpec, ...] = (
    TableSpec(
        name="category_translation",
        file="product_category_name_translation.csv",
        primary_key=("product_category_name",),
    ),
    TableSpec(
        name="geolocation",
        file="olist_geolocation_dataset.csv",
        primary_key=("geolocation_zip_code_prefix",),
        strings=("geolocation_zip_code_prefix",),
        cities=("geolocation_city",),
    ),
    TableSpec(
        name="customers",
        file="olist_customers_dataset.csv",
        primary_key=("customer_id",),
        strings=("customer_zip_code_prefix",),
        cities=("customer_city",),
    ),
    TableSpec(
        name="sellers",
        file="olist_sellers_dataset.csv",
        primary_key=("seller_id",),
        strings=("seller_zip_code_prefix",),
        cities=("seller_city",),
    ),
    TableSpec(
        name="products",
        file="olist_products_dataset.csv",
        primary_key=("product_id",),
        renames={
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        },
        ranges={
            "product_weight_g": (0, None),
            "product_length_cm": (0, None),
            "product_height_cm": (0, None),
            "product_width_cm": (0, None),
        },
        foreign_keys=(
            ForeignKey(
                "product_category_name",
                "category_translation",
                "product_category_name",
                on_orphan="null",
            ),
        ),
    ),
    TableSpec(
        name="orders",
        file="olist_orders_dataset.csv",
        primary_key=("order_id",),
        dates=(
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ),
        foreign_keys=(ForeignKey("customer_id", "customers", "customer_id"),),
    ),
    TableSpec(
        name="order_items",
        file="olist_order_items_dataset.csv",
        primary_key=("order_id", "order_item_id"),
        dates=("shipping_limit_date",),
        ranges={"price": (0, None), "freight_value": (0, None)},
        foreign_keys=(
            ForeignKey("order_id", "orders", "order_id"),
            ForeignKey("product_id", "products", "product_id"),
            ForeignKey("seller_id", "sellers", "seller_id"),
        ),
    ),
    TableSpec(
        name="order_payments",
        file="olist_order_payments_dataset.csv",
        primary_key=("order_id", "payment_sequential"),
        ranges={"payment_value": (0, None), "payment_installments": (0, None)},
        foreign_keys=(ForeignKey("order_id", "orders", "order_id"),),
    ),
    TableSpec(
        name="order_reviews",
        file="olist_order_reviews_dataset.csv",
        # review_id seul n'est pas unique dans la source : clé composite.
        primary_key=("review_id", "order_id"),
        dates=("review_creation_date", "review_answer_timestamp"),
        ranges={"review_score": (1, 5)},
        foreign_keys=(ForeignKey("order_id", "orders", "order_id"),),
    ),
)

SPECS: dict[str, TableSpec] = {spec.name: spec for spec in TABLES}
