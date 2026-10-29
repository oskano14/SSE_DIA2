"""Feature engineering du modèle de retard, partagé par l'entraînement et l'API.

Chaque feature correspond à une cause plausible de retard :
- distance client-vendeur : plus de kilomètres, plus d'étapes de transport ;
- délai promis : une promesse courte est plus difficile à tenir ;
- poids, volume, nombre d'articles : colis plus lourds ou fractionnés ;
- historique vendeur : un vendeur souvent en retard le reste ;
- mois et jour d'achat : pics d'activité (Black Friday, fêtes).
"""

import pandas as pd
from sqlalchemy import Engine

from shoppulse.config import SQL_DIR
from shoppulse.geo import haversine_km
from shoppulse.queries import run_query

FEATURES = [
    "distance_km",
    "same_state",
    "promised_days",
    "n_items",
    "total_price",
    "total_freight",
    "total_weight_g",
    "total_volume_cm3",
    "seller_prior_orders",
    "seller_late_rate",
    "purchase_month",
    "purchase_weekday",
]
TARGET = "is_late"
# Colonnes reprises telles quelles depuis la requête ou l'historique vendeur.
PASSTHROUGH = [
    "n_items",
    "total_price",
    "total_freight",
    "total_weight_g",
    "total_volume_cm3",
    "seller_prior_orders",
    "seller_late_rate",
]

# Lissage de l'historique vendeur : un vendeur sans passé reçoit le taux moyen,
# et son propre taux ne domine qu'après une dizaine de commandes.
SMOOTHING = 10


def load_delay_orders(engine: Engine) -> pd.DataFrame:
    """Une ligne par commande livrée, triée par date d'achat."""
    df = run_query(SQL_DIR / "features" / "delay_orders.sql", engine)
    numeric = df.columns.difference(
        ["order_id", "customer_state", "seller_state", "seller_id"]
        + ["order_purchase_timestamp", "order_estimated_delivery_date", TARGET]
    )
    df[numeric] = df[numeric].astype(float)
    df[TARGET] = df[TARGET].astype(bool)
    return df


def smoothed_rate(late: pd.Series, orders: pd.Series, prior: float) -> pd.Series:
    """Taux de retard lissé vers la moyenne globale (évite 0 % ou 100 % sur 1 cas)."""
    return (late + SMOOTHING * prior) / (orders + SMOOTHING)


def add_seller_history(df: pd.DataFrame) -> pd.DataFrame:
    """Historique de chaque vendeur calculé sur ses commandes ANTÉRIEURES uniquement.

    Approximation assumée : une commande antérieure peut ne pas encore être
    livrée au moment de l'achat courant (voir la note de limites).
    """
    df = df.sort_values("order_purchase_timestamp").copy()
    by_seller = df.groupby("seller_id")[TARGET]
    prior_orders = by_seller.cumcount()
    prior_late = by_seller.cumsum() - df[TARGET]
    df["seller_prior_orders"] = prior_orders
    df["seller_late_rate"] = smoothed_rate(prior_late, prior_orders, df[TARGET].mean())
    return df


def seller_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Historique final par vendeur, servi par l'API pour les nouvelles commandes."""
    stats = df.groupby("seller_id").agg(orders=(TARGET, "size"), late=(TARGET, "sum"))
    stats["late_rate"] = smoothed_rate(
        stats["late"], stats["orders"], df[TARGET].mean()
    )
    return stats[["orders", "late_rate"]]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Matrice de features à partir des colonnes brutes d'une commande."""
    purchase = pd.to_datetime(df["order_purchase_timestamp"])
    estimated = pd.to_datetime(df["order_estimated_delivery_date"])
    features = pd.DataFrame(index=df.index)
    features["distance_km"] = haversine_km(
        df["customer_lat"], df["customer_lng"], df["seller_lat"], df["seller_lng"]
    )
    features["same_state"] = (df["customer_state"] == df["seller_state"]).astype(int)
    features["promised_days"] = (
        estimated.dt.normalize() - purchase.dt.normalize()
    ).dt.days
    for column in PASSTHROUGH:
        features[column] = df[column].astype(float)
    features["purchase_month"] = purchase.dt.month
    features["purchase_weekday"] = purchase.dt.day_of_week
    return features[FEATURES]
