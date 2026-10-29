"""Segmentation clients : scores RFM (requête SQL 08) puis K-means sur R, F, M."""

from collections.abc import Hashable

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy import Engine

from shoppulse.queries import QUERIES_DIR, run_query

FEATURES = ["recency_days", "frequency", "monetary"]
N_SEGMENTS = 3
SEED = 42


def load_rfm(engine: Engine) -> pd.DataFrame:
    """Récence, fréquence et montant par client (customer_unique_id)."""
    return run_query(QUERIES_DIR / "08_rfm_scores.sql", engine)


def _scaled(rfm: pd.DataFrame) -> np.ndarray:
    # log1p : R, F et M sont très asymétriques ; K-means suppose des échelles proches.
    scaled: np.ndarray = StandardScaler().fit_transform(
        np.log1p(rfm[FEATURES].astype(float))
    )
    return scaled


def silhouette_by_k(
    rfm: pd.DataFrame, ks: range, sample_size: int = 10_000
) -> dict[int, float]:
    """Score de silhouette pour chaque nombre de segments (aide au choix de k)."""
    x = _scaled(rfm)
    scores = {}
    for k in ks:
        labels = KMeans(k, n_init=10, random_state=SEED).fit_predict(x)
        scores[k] = float(
            silhouette_score(x, labels, sample_size=sample_size, random_state=SEED)
        )
    return scores


def _persona_names(rfm: pd.DataFrame, clusters: np.ndarray) -> dict[Hashable, str]:
    """Nomme les 3 clusters par règle métier, indépendamment de leur numéro."""
    means = rfm.groupby(clusters)[["frequency", "recency_days"]].mean()
    loyal = means["frequency"].idxmax()
    recent, dormant = means.drop(index=loyal)["recency_days"].sort_values().index
    return {loyal: "Fidèles", recent: "Récents", dormant: "Endormis"}


def segment(rfm: pd.DataFrame) -> pd.Series:
    """Affecte chaque client à l'une des 3 personas."""
    clusters = KMeans(N_SEGMENTS, n_init=10, random_state=SEED).fit_predict(
        _scaled(rfm)
    )
    names = _persona_names(rfm, clusters)
    return pd.Series([names[c] for c in clusters], index=rfm.index, name="persona")


def profile_segments(rfm: pd.DataFrame, personas: pd.Series) -> pd.DataFrame:
    """Portrait chiffré de chaque persona."""
    grouped = rfm.groupby(personas)
    summary = grouped.agg(
        customers=("frequency", "size"),
        recency_days=("recency_days", "mean"),
        frequency=("frequency", "mean"),
        monetary=("monetary", "mean"),
        revenue=("monetary", "sum"),
    )
    summary["customer_share_pct"] = 100 * summary["customers"] / len(rfm)
    summary["revenue_share_pct"] = 100 * summary["revenue"] / rfm["monetary"].sum()
    return summary.round(1).sort_values("customers")


def campaign_revenue(
    customers: int, conversion_rate: float, avg_basket: float, discount: float = 0.0
) -> float:
    """CA additionnel attendu d'une campagne : cibles x conversion x panier net."""
    return customers * conversion_rate * avg_basket * (1 - discount)
