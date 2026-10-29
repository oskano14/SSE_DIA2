"""Extraction : lecture brute d'un CSV Olist selon sa spécification."""

from pathlib import Path

import pandas as pd

from shoppulse.etl.specs import TableSpec


def extract(spec: TableSpec, source_dir: Path) -> pd.DataFrame:
    """Lit le CSV d'une table en types nullables, sans aucune transformation."""
    path = source_dir / spec.file
    if not path.exists():
        raise FileNotFoundError(f"Fichier source manquant : {path}")
    df = pd.read_csv(
        path,
        encoding="utf-8-sig",  # le fichier de traduction contient un BOM
        dtype={column: "string" for column in spec.strings},
        dtype_backend="numpy_nullable",
    )
    return df.rename(columns=spec.renames)
