"""Sentiment des avis : données et baseline TF-IDF + régression logistique.

Stratégie linguistique : on entraîne directement sur le portugais.
- Environ 39 000 avis sont étiquetés par leur note : assez pour un modèle dédié.
- La traduction ajouterait un coût, de la latence et du bruit (argot, fautes).
- Un modèle multilingue de type transformer serait lourd pour une API servie sur CPU.

Ce module ne dépend pas de PyTorch : l'API l'importe sans charger le réseau.
"""

import re
import unicodedata

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sqlalchemy import Engine

from shoppulse.config import SQL_DIR
from shoppulse.queries import run_query

# Note 4-5 = positif, 1-2 = négatif. La note 3 est ambiguë et écartée.
POSITIVE_MIN, NEGATIVE_MAX = 4, 2
_NON_LETTERS = re.compile(r"[^a-z ]+")


def load_reviews(engine: Engine) -> pd.DataFrame:
    """Avis avec texte, étiquetés 1 (positif) / 0 (négatif), sans les notes 3."""
    df = run_query(SQL_DIR / "features" / "reviews.sql", engine)
    df = df[(df["review_score"] >= POSITIVE_MIN) | (df["review_score"] <= NEGATIVE_MAX)]
    return df.assign(label=(df["review_score"] >= POSITIVE_MIN).astype(int))


def normalize(text: str) -> str:
    """Minuscules, sans accents ni ponctuation : « Não chegou!! » -> « nao chegou »."""
    ascii_text = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore")
    return " ".join(_NON_LETTERS.sub(" ", ascii_text.decode()).split())


def tokenize(text: str) -> list[str]:
    """Mots et bigrammes : le bigramme « nao recebi » porte la négation."""
    words = normalize(text).split()
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:], strict=False)]


def baseline_model() -> Pipeline:
    """TF-IDF (mots + bigrammes) puis régression logistique pondérée.

    Les mots vides ne sont pas retirés : « não » et « nada » portent le sentiment.
    """
    return make_pipeline(
        TfidfVectorizer(
            preprocessor=normalize, ngram_range=(1, 2), min_df=2, sublinear_tf=True
        ),
        LogisticRegression(class_weight="balanced", max_iter=2000, C=4.0),
    )


def top_terms(model: Pipeline, n: int = 15) -> pd.DataFrame:
    """Termes les plus négatifs et les plus positifs selon la baseline."""
    vectorizer, classifier = model.steps[0][1], model.steps[1][1]
    terms = np.array(vectorizer.get_feature_names_out())
    order = np.argsort(classifier.coef_[0])
    return pd.DataFrame(
        {"négatif": terms[order[:n]], "positif": terms[order[-n:][::-1]]}
    )
