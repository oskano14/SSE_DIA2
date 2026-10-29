"""Tests de l'API sur des artefacts entraînés à partir de données synthétiques."""

from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from shoppulse.api import app
from shoppulse.features import TARGET
from shoppulse.training import (
    DELAY_FILE,
    SENTIMENT_FILE,
    load,
    save,
    train_delay,
    train_sentiment,
)

SELLER = "a" * 32
ORDER = {
    "customer_zip_code_prefix": "01310",
    "seller_id": SELLER,
    "purchase_timestamp": "2018-03-10T14:30:00",
    "estimated_delivery_date": "2018-03-20",
    "n_items": 1,
    "total_price": 100.0,
    "total_freight": 15.0,
}


def _orders(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    far = rng.random(n) < 0.5
    return pd.DataFrame(
        {
            "order_purchase_timestamp": pd.date_range(
                "2018-01-01", periods=n, freq="h"
            ),
            "order_estimated_delivery_date": pd.Timestamp("2018-03-01"),
            "seller_id": np.where(rng.random(n) < 0.5, SELLER, "b" * 32),
            "customer_state": np.where(far, "AM", "SP"),
            "seller_state": "SP",
            "customer_lat": np.where(far, -3.1, -23.5),
            "customer_lng": np.where(far, -60.0, -46.6),
            "seller_lat": -23.5,
            "seller_lng": -46.6,
            "n_items": 1.0,
            "total_price": rng.uniform(10, 200, n),
            "total_freight": rng.uniform(5, 50, n),
            "total_weight_g": rng.uniform(100, 5000, n),
            "total_volume_cm3": rng.uniform(100, 5000, n),
            TARGET: far & (rng.random(n) < 0.6),
        }
    )


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory) -> Iterator[TestClient]:
    directory = tmp_path_factory.mktemp("models")
    zips = pd.DataFrame(
        {
            "geolocation_zip_code_prefix": ["01310", "69005"],
            "geolocation_lat": [-23.5, -3.1],
            "geolocation_lng": [-46.6, -60.0],
            "geolocation_state": ["SP", "AM"],
        }
    )
    reviews = pd.DataFrame(
        {
            "text": ["amei, recomendo", "ótimo produto", "não recebi", "péssimo"] * 25,
            "label": [1, 1, 0, 0] * 25,
        }
    )
    save(train_delay(_orders(), zips), DELAY_FILE, directory)
    save(train_sentiment(reviews), SENTIMENT_FILE, directory)
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("MODELS_DIR", str(directory))
        with TestClient(app) as test_client:
            yield test_client


def test_artifact_round_trip(tmp_path: Path) -> None:
    save({"metrics": {"a": 1}}, "x.joblib", tmp_path)
    assert load("x.joblib", tmp_path) == {"metrics": {"a": 1}}


def test_health_exposes_model_metrics(client: TestClient) -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["delay_model"]["orders"] == 200
    assert "f1_macro_holdout" in body["sentiment_model"]


def test_predict_delay(client: TestClient) -> None:
    near = client.post("/predict/delay", json=ORDER)
    far = client.post(
        "/predict/delay", json={**ORDER, "customer_zip_code_prefix": "69005"}
    )
    assert near.status_code == far.status_code == 200
    assert set(near.json()) == {"late_probability", "high_risk", "threshold"}
    assert far.json()["late_probability"] > near.json()["late_probability"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("customer_zip_code_prefix", "123"),
        ("seller_id", "not-an-id"),
        ("n_items", 0),
        ("total_price", -5),
        ("estimated_delivery_date", "2018-03-01"),  # avant l'achat
    ],
)
def test_predict_delay_rejects_invalid_input(
    client: TestClient, field: str, value: object
) -> None:
    response = client.post("/predict/delay", json={**ORDER, field: value})
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("field", "value"),
    [("seller_id", "c" * 32), ("customer_zip_code_prefix", "99999")],
)
def test_predict_delay_unknown_reference(
    client: TestClient, field: str, value: str
) -> None:
    response = client.post("/predict/delay", json={**ORDER, field: value})
    assert response.status_code == 404


def test_predict_sentiment(client: TestClient) -> None:
    negative = client.post("/predict/sentiment", json={"text": "péssimo, não recebi"})
    positive = client.post("/predict/sentiment", json={"text": "amei, recomendo"})
    assert negative.json()["sentiment"] == "negative"
    assert positive.json()["sentiment"] == "positive"


def test_predict_sentiment_rejects_empty_text(client: TestClient) -> None:
    assert client.post("/predict/sentiment", json={"text": ""}).status_code == 422


def test_openapi_documents_one_endpoint_per_model(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/predict/delay", "/predict/sentiment", "/health"} <= set(paths)
