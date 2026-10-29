"""Accès aux requêtes d'analyse de sql/queries/ (tests, rapport, tableau de bord)."""

from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, text

from shoppulse.config import SQL_DIR

QUERIES_DIR = SQL_DIR / "queries"


def query_paths() -> list[Path]:
    """Requêtes d'analyse, triées par numéro."""
    return sorted(QUERIES_DIR.glob("*.sql"))


def describe(path: Path) -> str:
    """Question métier, lue dans le commentaire d'en-tête de la requête."""
    lines = []
    for line in path.read_text().splitlines():
        if not line.startswith("--") or "Techniques" in line:
            break
        lines.append(line.removeprefix("--").strip())
    return " ".join(lines).removeprefix("Question ").strip()


def run_query(path: Path, engine: Engine) -> pd.DataFrame:
    """Exécute une requête d'analyse et renvoie son résultat."""
    with engine.connect() as connection:
        return pd.read_sql(text(path.read_text()), connection)
