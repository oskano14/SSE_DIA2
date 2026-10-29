import pandas as pd
import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError

from shoppulse.db import get_engine
from shoppulse.etl.specs import ForeignKey, TableSpec


@pytest.fixture(scope="session")
def engine() -> Engine:
    """Base chargée par le pipeline ; les tests « db » sont ignorés sans base."""
    engine = get_engine()
    try:
        with engine.connect():
            pass
    except OperationalError:
        pytest.skip("PostgreSQL indisponible : lancer docker compose puis l'ETL")
    return engine


@pytest.fixture
def spec() -> TableSpec:
    return TableSpec(
        name="items",
        file="items.csv",
        primary_key=("order_id", "item_id"),
        dates=("shipped_at",),
        cities=("city",),
        ranges={"price": (0, None), "score": (1, 5)},
        foreign_keys=(ForeignKey("order_id", "orders", "order_id"),),
    )


@pytest.fixture
def items() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": pd.array(["o1", "o1", "o2", "o3", None], dtype="string"),
            "item_id": pd.array([1, 1, 1, 1, 1], dtype="Int64"),
            "shipped_at": pd.array(
                ["2018-01-01", "2018-01-01", "pas une date", None, "2018-02-01"],
                dtype="string",
            ),
            "city": pd.array(
                ["São Paulo", "São Paulo", " rio ", "BELÉM", "x"], dtype="string"
            ),
            "price": pd.array([10.0, 10.0, -1.0, 5.0, 3.0], dtype="Float64"),
            "score": pd.array([5, 5, 3, 9, 1], dtype="Int64"),
        }
    )
