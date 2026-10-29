"""Réseau de neurones de sentiment (PyTorch), à comparer à la baseline TF-IDF.

Architecture de type fastText : moyenne des embeddings des mots et bigrammes,
puis une couche cachée et une sortie logistique. Le modèle est léger, s'entraîne
en quelques secondes sur CPU et reste comparable à la baseline.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
from torch import nn

from shoppulse.sentiment import tokenize

SEED = 42
UNKNOWN = 0


def build_vocab(texts: Sequence[str], min_freq: int = 2) -> dict[str, int]:
    """Index des tokens vus au moins min_freq fois (0 est réservé aux inconnus)."""
    counts = Counter(token for text in texts for token in tokenize(text))
    kept = sorted(token for token, count in counts.items() if count >= min_freq)
    return {token: index for index, token in enumerate(kept, start=1)}


def encode(
    texts: Sequence[str], vocab: dict[str, int]
) -> tuple[torch.Tensor, torch.Tensor]:
    """Format EmbeddingBag : identifiants concaténés et position de chaque texte."""
    ids: list[int] = []
    offsets: list[int] = []
    for text in texts:
        offsets.append(len(ids))
        ids.extend(vocab.get(token, UNKNOWN) for token in tokenize(text) or [""])
    return torch.tensor(ids), torch.tensor(offsets)


class SentimentNet(nn.Module):
    def __init__(self, vocab_size: int, embedding_dim: int = 64, hidden: int = 32):
        super().__init__()
        self.embedding = nn.EmbeddingBag(vocab_size + 1, embedding_dim, mode="mean")
        self.head = nn.Sequential(
            nn.Linear(embedding_dim, hidden),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden, 1),
        )

    def forward(self, ids: torch.Tensor, offsets: torch.Tensor) -> torch.Tensor:
        logits: torch.Tensor = self.head(self.embedding(ids, offsets)).squeeze(1)
        return logits


@dataclass
class TrainedNet:
    model: SentimentNet
    vocab: dict[str, int]
    history: pd.DataFrame

    def predict_proba(self, texts: Sequence[str]) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            proba: np.ndarray = torch.sigmoid(
                self.model(*encode(texts, self.vocab))
            ).numpy()
        return proba


def _batches(n: int, size: int, generator: torch.Generator) -> list[torch.Tensor]:
    return list(torch.split(torch.randperm(n, generator=generator), size))


def _loss(
    model: SentimentNet,
    texts: Sequence[str],
    y: torch.Tensor,
    vocab: dict[str, int],
    loss_fn: nn.Module,
) -> float:
    model.eval()
    with torch.no_grad():
        return float(loss_fn(model(*encode(texts, vocab)), y))


def train_network(
    train_texts: Sequence[str],
    train_y: Sequence[int],
    val_texts: Sequence[str],
    val_y: Sequence[int],
    epochs: int = 12,
    batch_size: int = 256,
) -> TrainedNet:
    """Entraîne le réseau et garde l'époque de plus faible perte de validation."""
    torch.manual_seed(SEED)
    generator = torch.Generator().manual_seed(SEED)
    vocab = build_vocab(train_texts)
    model = SentimentNet(len(vocab))
    y_train = torch.tensor(train_y, dtype=torch.float32)
    y_val = torch.tensor(val_y, dtype=torch.float32)
    # Pondération des négatifs, minoritaires, comme class_weight="balanced".
    pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-3, weight_decay=1e-5)

    history, best_state, best_loss = [], model.state_dict(), float("inf")
    for epoch in range(1, epochs + 1):
        model.train()
        for batch in _batches(len(train_texts), batch_size, generator):
            optimizer.zero_grad()
            texts = [train_texts[i] for i in batch]
            loss = loss_fn(model(*encode(texts, vocab)), y_train[batch])
            loss.backward()
            optimizer.step()
        train_loss = _loss(model, train_texts, y_train, vocab, loss_fn)
        val_loss = _loss(model, val_texts, y_val, vocab, loss_fn)
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
        if val_loss < best_loss:
            best_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    return TrainedNet(model, vocab, pd.DataFrame(history).set_index("epoch"))
