"""Flow Prefect d'entraînement : base PostgreSQL -> artefacts dans models/.

Lancement (base chargée) : uv run python pipelines/train.py
"""

import pandas as pd
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from sqlalchemy import text

from shoppulse.db import get_engine
from shoppulse.features import load_delay_orders
from shoppulse.sentiment import load_reviews
from shoppulse.training import (
    DELAY_FILE,
    SENTIMENT_FILE,
    save,
    train_delay,
    train_sentiment,
)


@task(cache_policy=NO_CACHE)
def delay_task() -> dict[str, float]:
    engine = get_engine()
    with engine.connect() as connection:
        geolocation = pd.read_sql(text("SELECT * FROM geolocation"), connection)
    artifact = train_delay(load_delay_orders(engine), geolocation)
    save(artifact, DELAY_FILE)
    return dict(artifact["metrics"])


@task(cache_policy=NO_CACHE)
def sentiment_task() -> dict[str, float]:
    artifact = train_sentiment(load_reviews(get_engine()))
    save(artifact, SENTIMENT_FILE)
    return dict(artifact["metrics"])


@flow(name="train-models", log_prints=True)
def train_flow() -> dict[str, dict[str, float]]:
    logger = get_run_logger()
    metrics = {"delay": delay_task(), "sentiment": sentiment_task()}
    logger.info("Métriques : %s", metrics)
    return metrics


if __name__ == "__main__":
    train_flow()
