"""Échantillon cohérent des CSV Olist (< 1 Mo par fichier), versionnable.

Les fichiers gardent le format brut d'origine : le pipeline les traite
exactement comme les données complètes (utilisé par la CI).
"""

from pathlib import Path

import pandas as pd

from shoppulse.etl.specs import SPECS

# Assez de points par code postal pour exercer l'agrégation, sans dépasser 1 Mo.
GEO_POINTS_PER_ZIP = 5


def _read_raw(source_dir: Path, table: str) -> pd.DataFrame:
    path = source_dir / SPECS[table].file
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def make_sample(
    source_dir: Path, target_dir: Path, n_orders: int = 1000, seed: int = 42
) -> dict[str, int]:
    """Tire n_orders commandes et toutes les lignes qui s'y rattachent."""
    raw = {table: _read_raw(source_dir, table) for table in SPECS}
    orders = raw["orders"].sample(n=n_orders, random_state=seed)
    order_ids = set(orders["order_id"])
    items = raw["order_items"][raw["order_items"]["order_id"].isin(order_ids)]
    customers = raw["customers"][
        raw["customers"]["customer_id"].isin(orders["customer_id"])
    ]
    sellers = raw["sellers"][raw["sellers"]["seller_id"].isin(items["seller_id"])]
    zips = set(customers["customer_zip_code_prefix"]) | set(
        sellers["seller_zip_code_prefix"]
    )
    sample = {
        "category_translation": raw["category_translation"],
        "geolocation": raw["geolocation"][
            raw["geolocation"]["geolocation_zip_code_prefix"].isin(zips)
        ]
        .groupby("geolocation_zip_code_prefix")
        .head(GEO_POINTS_PER_ZIP),
        "customers": customers,
        "sellers": sellers,
        "products": raw["products"][
            raw["products"]["product_id"].isin(items["product_id"])
        ],
        "orders": orders,
        "order_items": items,
        "order_payments": raw["order_payments"][
            raw["order_payments"]["order_id"].isin(order_ids)
        ],
        "order_reviews": raw["order_reviews"][
            raw["order_reviews"]["order_id"].isin(order_ids)
        ],
    }
    target_dir.mkdir(parents=True, exist_ok=True)
    for table, df in sample.items():
        df.to_csv(target_dir / SPECS[table].file, index=False)
    return {table: len(df) for table, df in sample.items()}
