"""Chargement idempotent dans PostgreSQL.

Tout se fait dans une seule transaction : création du schéma si besoin,
vidage des tables puis COPY. Un échec laisse la base dans son état précédent ;
deux exécutions successives donnent exactement le même contenu.
"""

import io
from collections.abc import Mapping

import pandas as pd
from sqlalchemy import Engine

from shoppulse.config import SQL_DIR
from shoppulse.etl.specs import TABLES


def _copy(cursor: object, table: str, df: pd.DataFrame) -> None:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False)
    columns = ", ".join(df.columns)
    sql = f"COPY {table} ({columns}) FROM STDIN WITH (FORMAT csv)"
    with cursor.copy(sql) as copy:  # type: ignore[attr-defined]
        copy.write(buffer.getvalue())


def load(tables: Mapping[str, pd.DataFrame], engine: Engine) -> dict[str, int]:
    """Recharge intégralement les tables et renvoie le nombre de lignes chargées."""
    names = [spec.name for spec in TABLES]
    with engine.begin() as connection:
        connection.exec_driver_sql((SQL_DIR / "schema.sql").read_text())
        connection.exec_driver_sql(f"TRUNCATE {', '.join(names)} CASCADE")
        cursor = connection.connection.cursor()
        for name in names:  # ordre parent -> enfant imposé par TABLES
            _copy(cursor, name, tables[name])
    return {name: len(tables[name]) for name in names}
