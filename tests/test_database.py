"""Tests de données sur la base chargée par le pipeline (ignorés sans base)."""

from pathlib import Path

import pytest
from sqlalchemy import Engine, text

from shoppulse.etl.specs import TABLES
from shoppulse.queries import describe, query_paths, run_query

pytestmark = pytest.mark.db


def _scalar(engine: Engine, sql: str) -> int:
    with engine.connect() as connection:
        return int(connection.execute(text(sql)).scalar_one())


@pytest.mark.parametrize("table", [spec.name for spec in TABLES])
def test_every_table_is_loaded(engine: Engine, table: str) -> None:
    assert _scalar(engine, f"SELECT count(*) FROM {table}") > 0


def test_review_scores_are_in_range(engine: Engine) -> None:
    sql = "SELECT count(*) FROM order_reviews WHERE review_score NOT BETWEEN 1 AND 5"
    assert _scalar(engine, sql) == 0


def test_no_delivery_before_purchase(engine: Engine) -> None:
    sql = """SELECT count(*) FROM orders
             WHERE order_delivered_customer_date < order_purchase_timestamp"""
    assert _scalar(engine, sql) == 0


def test_every_order_has_items_or_is_not_delivered(engine: Engine) -> None:
    sql = """SELECT count(*) FROM orders AS o
             WHERE o.order_status = 'delivered'
               AND NOT EXISTS (SELECT 1 FROM order_items AS i
                               WHERE i.order_id = o.order_id)"""
    assert _scalar(engine, sql) <= 10  # quelques anomalies connues de la source


def test_there_are_eight_documented_queries() -> None:
    paths = query_paths()
    assert len(paths) == 8
    assert all(describe(path) for path in paths)


@pytest.mark.parametrize("path", query_paths(), ids=lambda path: path.stem)
def test_query_returns_rows(engine: Engine, path: Path) -> None:
    assert not run_query(path, engine).empty
