"""Exécute les 8 requêtes d'analyse et publie leurs résultats dans docs/.

Lancement (base chargée) : uv run python pipelines/sql_report.py
"""

from shoppulse.config import DOCS_DIR
from shoppulse.db import get_engine
from shoppulse.queries import describe, query_paths, run_query

PREVIEW_ROWS = 10


def build_report() -> str:
    engine = get_engine()
    sections = ["# Résultats des requêtes d'analyse (généré, ne pas éditer)"]
    for path in query_paths():
        result = run_query(path, engine)
        sections += [
            f"## [{path.stem}](../sql/queries/{path.name})",
            describe(path),
            result.head(PREVIEW_ROWS).to_markdown(index=False),
            f"_{len(result)} ligne(s) au total._",
        ]
    return "\n\n".join(sections) + "\n"


if __name__ == "__main__":
    (DOCS_DIR / "sql_results.md").write_text(build_report())
