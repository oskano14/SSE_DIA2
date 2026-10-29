from pathlib import Path

import pandas as pd
import pytest

from shoppulse.config import SAMPLE_DIR
from shoppulse.etl.clean import clean_all
from shoppulse.etl.extract import extract
from shoppulse.etl.quality import check, profile_all
from shoppulse.etl.sample import make_sample
from shoppulse.etl.specs import SPECS, TABLES


def test_extract_keeps_zip_leading_zero_and_strips_bom(tmp_path: Path) -> None:
    spec = SPECS["sellers"]
    (tmp_path / spec.file).write_text(
        "﻿seller_id,seller_zip_code_prefix,seller_city,seller_state\n"
        "s1,01037,sao paulo,SP\n",
        encoding="utf-8",
    )
    df = extract(spec, tmp_path)
    assert df.columns[0] == "seller_id"
    assert df.loc[0, "seller_zip_code_prefix"] == "01037"


def test_extract_applies_renames(tmp_path: Path) -> None:
    spec = SPECS["products"]
    pd.DataFrame(columns=["product_id", "product_name_lenght"]).to_csv(
        tmp_path / spec.file, index=False
    )
    assert "product_name_length" in extract(spec, tmp_path).columns


def test_extract_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        extract(SPECS["orders"], tmp_path)


def test_committed_sample_cleans_without_blocking_issue() -> None:
    """Test de données : l'échantillon versionné passe tous les contrôles."""
    raw = {spec.name: extract(spec, SAMPLE_DIR) for spec in TABLES}
    cleaned, _ = clean_all(raw)
    check(profile_all(cleaned))
    assert all(len(cleaned[spec.name]) for spec in TABLES)


def test_sample_files_are_under_one_megabyte() -> None:
    sizes = {path.name: path.stat().st_size for path in SAMPLE_DIR.glob("*.csv")}
    assert len(sizes) == len(TABLES)
    assert max(sizes.values()) < 1_000_000


def test_make_sample_is_consistent(tmp_path: Path) -> None:
    counts = make_sample(SAMPLE_DIR, tmp_path, n_orders=50)
    assert counts["orders"] == 50
    resampled = {spec.name: extract(spec, tmp_path) for spec in TABLES}
    cleaned, _ = clean_all(resampled)
    check(profile_all(cleaned))
