"""Audit d'équité : performances d'un classifieur par groupe (ex. région client)."""

import numpy as np
import pandas as pd


def group_metrics(
    y: pd.Series, predicted: np.ndarray, groups: pd.Series
) -> pd.DataFrame:
    """Par groupe : taux de retard, taux d'alerte, rappel, précision, faux positifs."""
    frame = pd.DataFrame(
        {"y": y.to_numpy(), "pred": predicted, "group": groups.to_numpy()}
    )
    rows = {}
    for name, g in frame.groupby("group"):
        positives, negatives = g["y"].sum(), (~g["y"]).sum()
        flagged = g["pred"].sum()
        true_pos = (g["y"] & g["pred"]).sum()
        rows[name] = {
            "orders": len(g),
            "late_rate": g["y"].mean(),
            "flag_rate": g["pred"].mean(),
            "recall": true_pos / positives if positives else np.nan,
            "precision": true_pos / flagged if flagged else np.nan,
            "false_positive_rate": (g["pred"] & ~g["y"]).sum() / negatives
            if negatives
            else np.nan,
        }
    return pd.DataFrame(rows).T.astype(float).round(3)


def disparity(metrics: pd.DataFrame, column: str) -> float:
    """Écart max/min d'une métrique entre groupes (1 = parfaite égalité)."""
    values = metrics[column].dropna()
    return float(values.max() / values.min())
