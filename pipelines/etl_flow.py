"""Flow Prefect de l'ETL Olist : extraction, nettoyage, contrôles, chargement.

Lancement : uv run python pipelines/etl_flow.py [dossier_source]
"""

import sys
from pathlib import Path

import pandas as pd
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from shoppulse.config import DOCS_DIR, PROJECT_ROOT, raw_dir
from shoppulse.db import get_engine
from shoppulse.etl.clean import CleaningStep, clean_all
from shoppulse.etl.extract import extract
from shoppulse.etl.load import load
from shoppulse.etl.quality import check, profile_all, render_report
from shoppulse.etl.specs import TABLES

Tables = dict[str, pd.DataFrame]


@task(cache_policy=NO_CACHE)
def extract_task(source_dir: Path) -> Tables:
    return {spec.name: extract(spec, source_dir) for spec in TABLES}


@task(cache_policy=NO_CACHE)
def clean_task(raw: Tables) -> tuple[Tables, list[CleaningStep]]:
    return clean_all(raw)


@task(cache_policy=NO_CACHE)
def quality_task(
    raw: Tables, cleaned: Tables, steps: list[CleaningStep], source_dir: Path
) -> str:
    """Contrôle bloquant puis rapport avant/après ; lève QualityError si KO."""
    after = profile_all(cleaned)
    check(after)
    source = source_dir.relative_to(PROJECT_ROOT, walk_up=True)
    return render_report(profile_all(raw), after, steps, source=str(source))


@task(cache_policy=NO_CACHE, retries=2, retry_delay_seconds=5)
def load_task(cleaned: Tables) -> dict[str, int]:
    return load(cleaned, get_engine())


@flow(name="olist-etl", log_prints=True)
def etl_flow(source_dir: Path | None = None) -> dict[str, int]:
    """Pipeline complet et rejouable : le résultat ne dépend que des CSV."""
    logger = get_run_logger()
    source_dir = source_dir or raw_dir()
    raw = extract_task(source_dir)
    cleaned, steps = clean_task(raw)
    report = quality_task(raw, cleaned, steps, source_dir)
    counts = load_task(cleaned)
    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "quality_report.md").write_text(report + "\n")
    logger.info("Lignes chargées : %s", counts)
    return counts


if __name__ == "__main__":
    etl_flow(PROJECT_ROOT / sys.argv[1] if len(sys.argv) > 1 else None)
