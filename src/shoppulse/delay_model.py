"""Modèle de prédiction du retard : baseline et deux algorithmes comparés.

Les classes sont déséquilibrées (environ 7 % de retards). On compare donc les
modèles sur la PR-AUC (average precision), le rappel et la précision, pas sur
l'exactitude.
"""

import numpy as np
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_validate
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 42
SCORING = ["average_precision", "roc_auc", "recall", "precision", "f1"]


def candidate_models() -> dict[str, ClassifierMixin]:
    """Baseline naïve et deux algorithmes pondérés contre le déséquilibre."""
    return {
        "baseline": DummyClassifier(strategy="prior"),
        "logistic_regression": make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=2000),
        ),
        "gradient_boosting": HistGradientBoostingClassifier(
            class_weight="balanced", random_state=SEED
        ),
    }


def folds() -> StratifiedKFold:
    return StratifiedKFold(5, shuffle=True, random_state=SEED)


def compare_models(x: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Validation croisée stratifiée à 5 plis : moyenne et écart-type par métrique."""
    rows = {}
    for name, model in candidate_models().items():
        scores = cross_validate(model, x, y, cv=folds(), scoring=SCORING)
        rows[name] = {
            f"{metric}_{stat}": getattr(scores[f"test_{metric}"], stat)()
            for metric in SCORING
            for stat in ("mean", "std")
        }
    return pd.DataFrame(rows).T.round(3)


def out_of_fold_proba(
    model: ClassifierMixin, x: pd.DataFrame, y: pd.Series
) -> np.ndarray:
    """Probabilités prédites sur des commandes jamais vues à l'entraînement."""
    proba: np.ndarray = cross_val_predict(
        model, x, y, cv=folds(), method="predict_proba"
    )[:, 1]
    return proba


def capture_rate(y: pd.Series, proba: np.ndarray, share: float) -> float:
    """Part des retards captés en contrôlant les `share` commandes les plus risquées."""
    top = proba >= np.quantile(proba, 1 - share)
    return float(y[top].sum() / y.sum())


def importance_table(
    model: ClassifierMixin, x: pd.DataFrame, y: pd.Series
) -> pd.Series:
    """Importance par permutation : perte de PR-AUC quand on brouille une variable."""
    result = permutation_importance(
        model,
        x,
        y,
        scoring="average_precision",
        n_repeats=5,
        random_state=SEED,
        n_jobs=-1,
    )
    return pd.Series(result.importances_mean, index=x.columns).sort_values()
