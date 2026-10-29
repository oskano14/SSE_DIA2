import numpy as np
import pandas as pd
import pytest

from shoppulse.sentiment import baseline_model, normalize, tokenize, top_terms
from shoppulse.sentiment_nn import build_vocab, encode, train_network

POSITIVE = ["produto ótimo, recomendo", "chegou rápido, amei", "muito bom", "perfeito"]
NEGATIVE = ["não recebi o produto", "péssimo, não recomendo", "veio quebrado", "ruim"]


@pytest.fixture
def corpus() -> pd.DataFrame:
    texts = (POSITIVE + NEGATIVE) * 10
    return pd.DataFrame({"text": texts, "label": ([1] * 4 + [0] * 4) * 10})


def test_normalize_strips_accents_case_and_punctuation() -> None:
    assert normalize("Não chegou!! Péssimo...") == "nao chegou pessimo"


def test_tokenize_adds_bigrams() -> None:
    assert tokenize("Não recebi") == ["nao", "recebi", "nao_recebi"]


def test_baseline_learns_polarity(corpus: pd.DataFrame) -> None:
    model = baseline_model().fit(corpus["text"], corpus["label"])
    proba = model.predict_proba(["não recomendo, péssimo", "amei, recomendo"])[:, 1]
    assert proba[0] < 0.5 < proba[1]
    terms = top_terms(model, n=3)
    assert "nao" in set(terms["négatif"])


def test_vocab_and_encoding() -> None:
    vocab = build_vocab(["a b", "a c"], min_freq=2)
    assert vocab == {"a": 1}
    ids, offsets = encode(["a b", ""], vocab)
    assert ids.tolist() == [1, 0, 0, 0]  # « b » et « a_b » inconnus, texte vide -> 0
    assert offsets.tolist() == [0, 3]


def test_network_trains_and_predicts(corpus: pd.DataFrame) -> None:
    texts, labels = list(corpus["text"]), list(corpus["label"])
    trained = train_network(texts, labels, texts, labels, epochs=30, batch_size=16)
    assert list(trained.history.columns) == ["train_loss", "val_loss"]
    assert (
        trained.history["train_loss"].iloc[-1] < trained.history["train_loss"].iloc[0]
    )
    proba = trained.predict_proba(["não recebi, péssimo", "amei, perfeito"])
    assert np.all((proba >= 0) & (proba <= 1))
    assert proba[0] < proba[1]
