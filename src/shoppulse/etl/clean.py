"""Nettoyage traçable : chaque règle est une fonction qui renvoie le nombre
de lignes ou cellules affectées, consigné dans un journal.

La première ligne de la docstring d'une règle sert de description dans le
rapport qualité.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import pandas as pd

from shoppulse.etl.specs import TABLES, TableSpec

# Emprise géographique du Brésil (lat_min, lat_max, lng_min, lng_max).
BRAZIL_BOUNDS = (-33.75, 5.27, -73.99, -34.79)

Rule = Callable[[pd.DataFrame, TableSpec], tuple[pd.DataFrame, int]]


@dataclass(frozen=True)
class CleaningStep:
    table: str
    rule: str
    description: str
    affected: int


def _changed_cells(before: pd.Series, after: pd.Series) -> int:
    same = (before == after).fillna(False) | (before.isna() & after.isna())
    return int((~same).sum())


# --- Règles de préparation -------------------------------------------------


def strip_strings(df: pd.DataFrame, spec: TableSpec) -> tuple[pd.DataFrame, int]:
    """Supprime les espaces superflus et remplace les textes vides par NULL."""
    df = df.copy()
    affected = 0
    columns: list[str] = df.select_dtypes(include="string").columns.tolist()
    for column in columns:
        cleaned = df[column].str.strip().replace("", pd.NA)
        affected += _changed_cells(df[column], cleaned)
        df[column] = cleaned
    return df, affected


def normalize_cities(df: pd.DataFrame, spec: TableSpec) -> tuple[pd.DataFrame, int]:
    """Normalise les noms de ville : minuscules et sans accents."""
    df = df.copy()
    affected = 0
    for column in spec.cities:
        cleaned = (
            df[column]
            .str.normalize("NFKD")
            .str.encode("ascii", "ignore")
            .str.decode("ascii")
            .str.lower()
            .astype("string")
        )
        affected += _changed_cells(df[column], cleaned)
        df[column] = cleaned
    return df, affected


def parse_dates(df: pd.DataFrame, spec: TableSpec) -> tuple[pd.DataFrame, int]:
    """Convertit les colonnes de dates ; une date illisible devient NULL."""
    df = df.copy()
    affected = 0
    for column in spec.dates:
        parsed = pd.to_datetime(df[column], errors="coerce")
        affected += int((df[column].notna() & parsed.isna()).sum())
        df[column] = parsed
    return df, affected


# --- Règles spécifiques ----------------------------------------------------


def drop_outside_brazil(df: pd.DataFrame, spec: TableSpec) -> tuple[pd.DataFrame, int]:
    """Supprime les coordonnées GPS situées hors du Brésil."""
    lat_min, lat_max, lng_min, lng_max = BRAZIL_BOUNDS
    inside = df["geolocation_lat"].between(lat_min, lat_max) & df[
        "geolocation_lng"
    ].between(lng_min, lng_max)
    return df[inside], int((~inside).sum())


def aggregate_by_zip(df: pd.DataFrame, spec: TableSpec) -> tuple[pd.DataFrame, int]:
    """Agrège les points GPS en un point médian par préfixe de code postal."""
    aggregated = (
        df.groupby("geolocation_zip_code_prefix", as_index=False)
        .agg(
            geolocation_lat=("geolocation_lat", "median"),
            geolocation_lng=("geolocation_lng", "median"),
            geolocation_city=("geolocation_city", "first"),
            geolocation_state=("geolocation_state", "first"),
        )
        .astype({"geolocation_city": "string", "geolocation_state": "string"})
    )
    return aggregated, len(df) - len(aggregated)


def null_impossible_dates(
    df: pd.DataFrame, spec: TableSpec
) -> tuple[pd.DataFrame, int]:
    """Vide les dates d'étape antérieures à la date d'achat."""
    df = df.copy()
    affected = 0
    purchase = df["order_purchase_timestamp"]
    for column in spec.dates:
        if column == "order_purchase_timestamp":
            continue
        impossible = (df[column] < purchase).fillna(False)
        affected += int(impossible.sum())
        df.loc[impossible, column] = pd.NaT
    return df, affected


# --- Règles d'intégrité ----------------------------------------------------


def drop_exact_duplicates(
    df: pd.DataFrame, spec: TableSpec
) -> tuple[pd.DataFrame, int]:
    """Supprime les lignes strictement identiques."""
    deduplicated = df.drop_duplicates()
    return deduplicated, len(df) - len(deduplicated)


def drop_null_keys(df: pd.DataFrame, spec: TableSpec) -> tuple[pd.DataFrame, int]:
    """Supprime les lignes dont la clé primaire est incomplète."""
    complete = df[list(spec.primary_key)].notna().all(axis=1)
    return df[complete], int((~complete).sum())


def drop_duplicate_keys(df: pd.DataFrame, spec: TableSpec) -> tuple[pd.DataFrame, int]:
    """Garde la première occurrence de chaque clé primaire."""
    deduplicated = df.drop_duplicates(subset=list(spec.primary_key))
    return deduplicated, len(df) - len(deduplicated)


def drop_out_of_range(df: pd.DataFrame, spec: TableSpec) -> tuple[pd.DataFrame, int]:
    """Supprime les lignes dont une valeur sort de son domaine autorisé."""
    valid = pd.Series(True, index=df.index)
    for column, (low, high) in spec.ranges.items():
        if low is not None:
            valid &= ~(df[column] < low).fillna(False)
        if high is not None:
            valid &= ~(df[column] > high).fillna(False)
    return df[valid], int((~valid).sum())


PREPARE_RULES: tuple[Rule, ...] = (strip_strings, normalize_cities, parse_dates)
SPECIFIC_RULES: dict[str, tuple[Rule, ...]] = {
    "geolocation": (drop_outside_brazil, aggregate_by_zip),
    "orders": (null_impossible_dates,),
}
INTEGRITY_RULES: tuple[Rule, ...] = (
    drop_exact_duplicates,
    drop_null_keys,
    drop_duplicate_keys,
    drop_out_of_range,
)


def resolve_orphans(
    df: pd.DataFrame, spec: TableSpec, parents: Mapping[str, pd.DataFrame]
) -> tuple[pd.DataFrame, list[CleaningStep]]:
    """Traite les références vers une ligne parente absente (selon on_orphan)."""
    steps = []
    for fk in spec.foreign_keys:
        known = parents[fk.parent][fk.parent_column]
        orphan = df[fk.column].notna() & ~df[fk.column].isin(known)
        if fk.on_orphan == "null":
            df = df.copy()
            df.loc[orphan, fk.column] = pd.NA
            action = "vide la référence"
        else:
            df = df[~orphan]
            action = "supprime la ligne"
        steps.append(
            CleaningStep(
                spec.name,
                f"orphan_{fk.column}",
                f"{fk.column} absent de {fk.parent} : {action}.",
                int(orphan.sum()),
            )
        )
    return df, steps


def clean_table(
    df: pd.DataFrame, spec: TableSpec, parents: Mapping[str, pd.DataFrame]
) -> tuple[pd.DataFrame, list[CleaningStep]]:
    """Applique toutes les règles d'une table et renvoie le journal associé."""
    rules = PREPARE_RULES + SPECIFIC_RULES.get(spec.name, ()) + INTEGRITY_RULES
    steps = []
    for rule in rules:
        df, affected = rule(df, spec)
        description = (rule.__doc__ or "").strip().splitlines()[0]
        steps.append(CleaningStep(spec.name, rule.__name__, description, affected))
    df, orphan_steps = resolve_orphans(df, spec, parents)
    return df.reset_index(drop=True), steps + orphan_steps


def clean_all(
    raw: Mapping[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], list[CleaningStep]]:
    """Nettoie toutes les tables, parents d'abord, et renvoie le journal complet."""
    cleaned: dict[str, pd.DataFrame] = {}
    journal: list[CleaningStep] = []
    for spec in TABLES:
        cleaned[spec.name], steps = clean_table(raw[spec.name], spec, cleaned)
        journal += steps
    return cleaned, journal
