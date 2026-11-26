import pandas as pd
import pytest

from src.transform.clean_prices import clean_prices, parse_unit_kg


def make_row(**changes):
    row = {
        "date": "2021-06-15", "admin1": "ASHANTI", "admin2": "KUMASI",
        "market": "Kumasi", "market_id": "10", "latitude": "6.69",
        "longitude": "-1.62", "category": "cereals and tubers",
        "commodity": "Maize", "commodity_id": "1", "unit": "KG",
        "priceflag": "aggregate", "pricetype": "Retail", "currency": "GHS",
        "price": "4.00", "usdprice": "0.70", "_source_file": "test.csv",
    }
    row.update(changes)
    return row


def run(*rows):
    clean, checker = clean_prices(pd.DataFrame(rows))
    failed = [r["check_name"] for r in checker.rejected_records()]
    return clean, failed


@pytest.mark.parametrize("unit, expected", [("KG", 1.0), ("100 KG", 100.0), ("50 kg", 50.0)])
def test_parse_unit_kg_reads_pack_sizes(unit, expected):
    assert parse_unit_kg(unit) == expected


def test_parse_unit_kg_unknown_unit_is_nan():
    assert pd.isna(parse_unit_kg("L"))


def test_good_row_passes_and_is_tagged_real():
    clean, failed = run(make_row())
    assert len(clean) == 1 and failed == []
    assert clean["price_per_kg_ghs"].iloc[0] == 4.0
    assert clean["data_origin"].iloc[0] == "real"


def test_100kg_price_is_converted_to_per_kg():
    clean, _ = run(make_row(unit="100 KG", price="400"))
    assert clean["price_per_kg_ghs"].iloc[0] == 4.0


def test_out_of_scope_rows_are_filtered_not_rejected():
    clean, failed = run(make_row(commodity="Cassava"), make_row(date="2019-05-15"))
    assert clean.empty and failed == []


def test_empty_price_is_rejected_by_not_null():
    clean, failed = run(make_row(price=""))
    assert clean.empty and failed == ["not_null"]


def test_non_numeric_price_is_rejected_by_valid_format():
    clean, failed = run(make_row(price="abc"))
    assert clean.empty and failed == ["valid_format"]


def test_unknown_unit_is_rejected_by_valid_format():
    clean, failed = run(make_row(unit="L"))
    assert clean.empty and failed == ["valid_format"]


def test_absurd_price_is_rejected_by_price_range():
    clean, failed = run(make_row(price="5000"))
    assert clean.empty and failed == ["price_range"]


def test_market_outside_ghana_is_rejected_by_reference_check():
    clean, failed = run(make_row(latitude="51.5", longitude="-0.1"))
    assert clean.empty and failed == ["reference_check"]


def test_duplicate_keeps_the_actual_price():
    first = make_row(priceflag="aggregate", price="4.00")
    second = make_row(priceflag="actual", price="5.00")
    clean, failed = run(first, second)
    assert failed == ["duplicates"]
    assert len(clean) == 1 and clean["price_flag"].iloc[0] == "actual"