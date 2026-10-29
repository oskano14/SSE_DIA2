import numpy as np
import pandas as pd
import pytest

from shoppulse.delay_model import capture_rate, compare_models
from shoppulse.fairness import disparity, group_metrics
from shoppulse.features import (
    FEATURES,
    TARGET,
    add_seller_history,
    build_features,
    seller_stats,
)


@pytest.fixture
def orders() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_purchase_timestamp": pd.to_datetime(
                ["2018-01-01 10:00", "2018-01-02 09:00", "2018-01-03 08:00"]
            ),
            "order_estimated_delivery_date": pd.to_datetime(
                ["2018-01-11", "2018-01-05", "2018-01-20"]
            ),
            "seller_id": ["s1", "s1", "s2"],
            "customer_state": ["SP", "RJ", "SP"],
            "seller_state": ["SP", "SP", "SP"],
            "customer_lat": [-23.55, -22.91, -23.55],
            "customer_lng": [-46.63, -43.17, -46.63],
            "seller_lat": [-23.55, -23.55, -23.55],
            "seller_lng": [-46.63, -46.63, -46.63],
            "n_items": [1, 2, 1],
            "total_price": [10.0, 20.0, 30.0],
            "total_freight": [5.0, 6.0, 7.0],
            "total_weight_g": [100.0, np.nan, 300.0],
            "total_volume_cm3": [1000.0, 2000.0, 3000.0],
            TARGET: [True, False, False],
        }
    )


def test_seller_history_uses_only_past_orders(orders: pd.DataFrame) -> None:
    history = add_seller_history(orders)
    assert history["seller_prior_orders"].tolist() == [0, 1, 0]
    # 2e commande de s1 : 1 retard passé, lissé vers la moyenne globale (1/3).
    expected = (1 + 10 * (1 / 3)) / (1 + 10)
    assert history["seller_late_rate"].iloc[1] == pytest.approx(expected)
    assert history["seller_late_rate"].iloc[0] == pytest.approx(1 / 3)


def test_build_features(orders: pd.DataFrame) -> None:
    features = build_features(add_seller_history(orders))
    assert list(features.columns) == FEATURES
    assert features["promised_days"].tolist() == [10, 3, 17]
    assert features["same_state"].tolist() == [1, 0, 1]
    assert features.loc[0, "distance_km"] == pytest.approx(0)
    assert features.loc[1, "distance_km"] == pytest.approx(360, abs=10)


def test_seller_stats(orders: pd.DataFrame) -> None:
    stats = seller_stats(orders)
    assert stats.loc["s1", "orders"] == 2
    assert stats.loc["s2", "late_rate"] < stats.loc["s1", "late_rate"]


def test_compare_models_beats_baseline() -> None:
    rng = np.random.default_rng(0)
    x = pd.DataFrame({"signal": rng.normal(size=400), "noise": rng.normal(size=400)})
    y = pd.Series(x["signal"] + rng.normal(scale=0.5, size=400) > 1.2)
    table = compare_models(x, y)
    assert set(table.index) == {"baseline", "logistic_regression", "gradient_boosting"}
    assert (
        table.loc["logistic_regression", "average_precision_mean"]
        > table.loc["baseline", "average_precision_mean"]
    )


def test_capture_rate() -> None:
    y = pd.Series([True, False, False, False, True, False, False, False, False, False])
    proba = np.array([0.9, 0.1, 0.2, 0.1, 0.3, 0.1, 0.1, 0.1, 0.1, 0.1])
    assert capture_rate(y, proba, share=0.1) == pytest.approx(0.5)


def test_group_metrics_and_disparity() -> None:
    y = pd.Series([True, False, True, False])
    predicted = np.array([True, True, False, False])
    groups = pd.Series(["A", "A", "B", "B"])
    metrics = group_metrics(y, predicted, groups)
    assert metrics.loc["A", "recall"] == 1.0
    assert metrics.loc["A", "false_positive_rate"] == 1.0
    assert metrics.loc["B", "recall"] == 0.0
    assert disparity(metrics, "late_rate") == pytest.approx(1.0)
