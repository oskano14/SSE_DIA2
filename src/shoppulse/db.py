"""Accès à la base PostgreSQL."""

from functools import cache

from sqlalchemy import Engine, create_engine

from shoppulse.config import database_url


@cache
def get_engine() -> Engine:
    """Moteur SQLAlchemy partagé par tout le projet."""
    return create_engine(database_url(), pool_pre_ping=True)
