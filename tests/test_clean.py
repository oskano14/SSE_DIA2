import pandas as pd
import pytest

from shoppulse.etl import clean
from shoppulse.etl.specs import SPECS, ForeignKey, TableSpec


def test_strip_strings_turns_blank_into_null(
    items: pd.DataFrame, spec: TableSpec
) -> None:
    cities = pd.array(["a ", "", "b", "c", "d"], dtype="string")
    df, affected = clean.strip_strings(items.assign(city=cities), spec)
    assert df["city"].isna().tolist() == [False, True, False, False, False]
    assert df.loc[0, "city"] == "a"
    assert affected == 2  # "a " rogné, "" vidé


def test_normalize_cities_removes_accents_and_case(
    items: pd.DataFrame, spec: TableSpec
) -> None:
    df, affected = clean.normalize_cities(items, spec)
    assert df["city"].tolist()[:4] == ["sao paulo", "sao paulo", " rio ", "belem"]
    assert affected == 3


def test_parse_dates_counts_unreadable_values(
    items: pd.DataFrame, spec: TableSpec
) -> None:
    df, affected = clean.parse_dates(items, spec)
    assert pd.api.types.is_datetime64_any_dtype(df["shipped_at"])
    assert affected == 1


def test_integrity_rules(items: pd.DataFrame, spec: TableSpec) -> None:
    df, duplicates = clean.drop_exact_duplicates(items, spec)
    assert duplicates == 1
    df, null_keys = clean.drop_null_keys(df, spec)
    assert null_keys == 1
    df, out_of_range = clean.drop_out_of_range(df, spec)
    assert out_of_range == 2  # prix négatif et note 9
    assert df["order_id"].tolist() == ["o1"]


def test_drop_duplicate_keys_keeps_first(spec: TableSpec) -> None:
    df = pd.DataFrame({"order_id": ["o1", "o1"], "item_id": [1, 1], "v": [1, 2]})
    result, affected = clean.drop_duplicate_keys(df, spec)
    assert result["v"].tolist() == [1]
    assert affected == 1


@pytest.mark.parametrize(
    ("on_orphan", "expected_nulls"), [("drop", [False]), ("null", [False, True])]
)
def test_resolve_orphans(on_orphan: str, expected_nulls: list[bool]) -> None:
    spec = TableSpec(
        name="items",
        file="",
        primary_key=("item_id",),
        foreign_keys=(ForeignKey("order_id", "orders", "order_id", on_orphan),),
    )
    df = pd.DataFrame(
        {"item_id": [1, 2], "order_id": pd.array(["o1", "zz"], dtype="string")}
    )
    parents = {"orders": pd.DataFrame({"order_id": ["o1"]})}
    result, steps = clean.resolve_orphans(df, spec, parents)
    assert result["order_id"].isna().tolist() == expected_nulls
    assert steps[0].affected == 1


def test_geolocation_rules() -> None:
    spec = SPECS["geolocation"]
    df = pd.DataFrame(
        {
            "geolocation_zip_code_prefix": ["01037", "01037", "01037", "99999"],
            "geolocation_lat": [-23.0, -23.2, -23.4, 40.0],  # 40 : hors Brésil
            "geolocation_lng": [-46.0, -46.2, -46.4, -3.0],
            "geolocation_city": ["sp", "sp", "sp", "madrid"],
            "geolocation_state": ["SP", "SP", "SP", "XX"],
        }
    )
    df, outside = clean.drop_outside_brazil(df, spec)
    assert outside == 1
    df, merged = clean.aggregate_by_zip(df, spec)
    assert merged == 2
    assert df.loc[0, "geolocation_lat"] == pytest.approx(-23.2)


def test_null_impossible_dates() -> None:
    spec = SPECS["orders"]
    df = pd.DataFrame({column: pd.to_datetime(["2018-01-10"]) for column in spec.dates})
    df["order_delivered_customer_date"] = pd.to_datetime(["2018-01-01"])
    result, affected = clean.null_impossible_dates(df, spec)
    assert affected == 1
    assert pd.isna(result.loc[0, "order_delivered_customer_date"])


def test_clean_table_logs_every_rule(items: pd.DataFrame, spec: TableSpec) -> None:
    parents = {"orders": pd.DataFrame({"order_id": ["o1", "o3"]})}
    result, steps = clean.clean_table(items, spec, parents)
    assert result["order_id"].tolist() == ["o1"]
    assert [step.rule for step in steps][-1] == "orphan_order_id"
    assert all(step.description for step in steps)
