"""Entraînement final des modèles servis par l'API et sauvegarde des artefacts.

Un artefact est un dictionnaire sérialisé avec joblib. Il contient le modèle et
tout ce dont l'API a besoin pour prédire sans base de données : les tables de
correspondance (vendeurs, codes postaux), le seuil d'alerte et les métriques.
"""

import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.metrics import average_precision_score, f1_score
from sklearn.model_selection import train_test_split

from shoppulse.config import PROJECT_ROOT
from shoppulse.delay_model import candidate_models, capture_rate, out_of_fold_proba
from shoppulse.features import TARGET, add_seller_history, build_features, seller_stats
from shoppulse.sentiment import baseline_model

# Part des commandes signalées « risque élevé » (choix opérationnel, notebook 03).
ALERT_SHARE = 0.10
DELAY_FILE, SENTIMENT_FILE = "delay.joblib", "sentiment.joblib"

Artifact = dict[str, Any]


def models_dir() -> Path:
    return PROJECT_ROOT / os.environ.get("MODELS_DIR", "models")


def train_delay(orders: pd.DataFrame, geolocation: pd.DataFrame) -> Artifact:
    """Gradient boosting final, seuil d'alerte et tables de correspondance."""
    history = add_seller_history(orders)
    x, y = build_features(history), history[TARGET]
    model = candidate_models()["gradient_boosting"]
    proba = out_of_fold_proba(model, x, y)
    threshold = float(pd.Series(proba).quantile(1 - ALERT_SHARE))
    sellers = seller_stats(orders).join(
        orders.groupby("seller_id")[
            ["seller_lat", "seller_lng", "seller_state"]
        ].first()
    )
    zips = geolocation.set_index("geolocation_zip_code_prefix")[
        ["geolocation_lat", "geolocation_lng", "geolocation_state"]
    ]
    return {
        "model": model.fit(x, y),
        "threshold": threshold,
        "sellers": sellers,
        "zips": zips,
        "metrics": {
            "orders": len(x),
            "late_rate": float(y.mean()),
            "pr_auc_cv": float(average_precision_score(y, proba)),
            "late_captured_at_alert_share": capture_rate(y, proba, ALERT_SHARE),
        },
    }


def train_sentiment(reviews: pd.DataFrame) -> Artifact:
    """Baseline TF-IDF : évaluée sur 20 % gardés de côté, puis réentraînée sur tout."""
    train, test = train_test_split(
        reviews, test_size=0.2, stratify=reviews["label"], random_state=42
    )
    holdout = baseline_model().fit(train["text"], train["label"])
    f1 = f1_score(test["label"], holdout.predict(test["text"]), average="macro")
    return {
        "model": baseline_model().fit(reviews["text"], reviews["label"]),
        "metrics": {"reviews": len(reviews), "f1_macro_holdout": float(f1)},
    }


def save(artifact: Artifact, name: str, directory: Path | None = None) -> Path:
    directory = directory or models_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    joblib.dump(artifact, path)
    return path


def load(name: str, directory: Path | None = None) -> Artifact:
    artifact: Artifact = joblib.load((directory or models_dir()) / name)
    return artifact
