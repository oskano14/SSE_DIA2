"""Contrôles qualité : profil d'une table, contrôles bloquants et rapport."""

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

import pandas as pd

from shoppulse.etl.clean import (
    CleaningStep,
    drop_duplicate_keys,
    drop_null_keys,
    drop_out_of_range,
)
from shoppulse.etl.specs import TABLES, TableSpec


class QualityError(Exception):
    """Levée quand une table nettoyée viole un contrôle bloquant."""


@dataclass(frozen=True)
class TableProfile:
    table: str
    rows: int
    null_keys: int
    duplicate_keys: int
    out_of_range: int
    orphans: int
    null_rate: float


BLOCKING_CHECKS = ("null_keys", "duplicate_keys", "out_of_range", "orphans")


def count_orphans(
    df: pd.DataFrame, spec: TableSpec, parents: Mapping[str, pd.DataFrame]
) -> int:
    """Nombre de références vers une ligne parente absente."""
    return sum(
        int(
            (
                df[fk.column].notna()
                & ~df[fk.column].isin(parents[fk.parent][fk.parent_column])
            ).sum()
        )
        for fk in spec.foreign_keys
    )


def profile(
    df: pd.DataFrame, spec: TableSpec, parents: Mapping[str, pd.DataFrame]
) -> TableProfile:
    """Mesure les indicateurs qualité d'une table."""
    return TableProfile(
        table=spec.name,
        rows=len(df),
        null_keys=drop_null_keys(df, spec)[1],
        duplicate_keys=drop_duplicate_keys(df, spec)[1],
        out_of_range=drop_out_of_range(df, spec)[1],
        orphans=count_orphans(df, spec, parents),
        null_rate=round(float(df.isna().mean().mean()), 4) if len(df) else 0.0,
    )


def profile_all(tables: Mapping[str, pd.DataFrame]) -> list[TableProfile]:
    """Profil de chaque table, les orphelins étant mesurés dans le même lot."""
    return [profile(tables[spec.name], spec, tables) for spec in TABLES]


def check(profiles: Sequence[TableProfile]) -> None:
    """Lève QualityError si une table nettoyée viole un contrôle bloquant."""
    failures = [
        f"{p.table}.{name} = {getattr(p, name)}"
        for p in profiles
        for name in BLOCKING_CHECKS
        if getattr(p, name)
    ]
    if failures:
        raise QualityError("Contrôles bloquants en échec : " + ", ".join(failures))


def _markdown_table(rows: Sequence[Mapping[str, object]]) -> str:
    headers = list(rows[0])
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(row[h]) for h in headers) + " |" for row in rows]
    return "\n".join(lines)


def render_report(
    before: Sequence[TableProfile],
    after: Sequence[TableProfile],
    steps: Sequence[CleaningStep],
    source: str,
) -> str:
    """Rapport Markdown : indicateurs avant/après et journal des règles."""
    comparison = [
        {
            "table": b.table,
            "lignes avant": b.rows,
            "lignes après": a.rows,
            "clés dupliquées avant": b.duplicate_keys,
            "hors domaine avant": b.out_of_range,
            "orphelins avant": b.orphans,
            "taux de NULL avant": b.null_rate,
            "taux de NULL après": a.null_rate,
        }
        for b, a in zip(before, after, strict=True)
    ]
    journal = [asdict(step) for step in steps if step.affected]
    return "\n\n".join(
        [
            "# Rapport qualité (généré par le pipeline, ne pas éditer)",
            f"Source : `{source}`",
            "## Indicateurs avant / après nettoyage",
            _markdown_table(comparison),
            "Après nettoyage, tous les contrôles bloquants valent 0 : "
            "clés nulles, clés dupliquées, valeurs hors domaine, orphelins.",
            "## Journal des règles appliquées (règles ayant eu un effet)",
            _markdown_table(journal) if journal else "Aucune règle n'a eu d'effet.",
        ]
    )
