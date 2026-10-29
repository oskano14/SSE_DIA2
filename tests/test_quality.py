import pandas as pd
import pytest

from shoppulse.etl.clean import CleaningStep
from shoppulse.etl.quality import QualityError, check, profile, render_report
from shoppulse.etl.specs import TableSpec


def test_profile_measures_raw_problems(items: pd.DataFrame, spec: TableSpec) -> None:
    parents = {"orders": pd.DataFrame({"order_id": ["o1"]})}
    result = profile(items, spec, parents)
    assert result.rows == 5
    assert result.null_keys == 1
    assert result.duplicate_keys == 1
    assert result.out_of_range == 2
    assert result.orphans == 2  # o2 et o3


def test_check_raises_on_blocking_issue(items: pd.DataFrame, spec: TableSpec) -> None:
    bad = profile(items, spec, {"orders": pd.DataFrame({"order_id": ["o1"]})})
    with pytest.raises(QualityError, match="duplicate_keys"):
        check([bad])


def test_check_passes_on_clean_table(spec: TableSpec) -> None:
    df = pd.DataFrame(
        {"order_id": ["o1"], "item_id": [1], "price": [1.0], "score": [3]}
    )
    check([profile(df, spec, {"orders": df})])


def test_report_contains_before_after_and_journal(
    items: pd.DataFrame, spec: TableSpec
) -> None:
    parents = {"orders": pd.DataFrame({"order_id": ["o1"]})}
    before = profile(items, spec, parents)
    after = profile(items.head(1), spec, parents)
    steps = [
        CleaningStep("items", "rule_a", "Fait A.", 3),
        CleaningStep("items", "rule_b", "Sans effet.", 0),
    ]
    report = render_report([before], [after], steps, source="data/raw")
    assert "| items | 5 | 1 |" in report
    assert "rule_a" in report
    assert "rule_b" not in report
