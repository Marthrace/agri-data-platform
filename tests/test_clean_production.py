import pandas as pd

from src.transform.clean_production import clean_production


def make_row(**changes):
    row = {
        "item": "Maize (corn)", "element": "Production", "year": "2020",
        "unit": "t", "value": "1000", "_source_file": "test.csv",
    }
    row.update(changes)
    return row


def run(*rows):
    clean, checker = clean_production(pd.DataFrame(rows))
    failed = [r["check_name"] for r in checker.rejected_records()]
    return clean, failed


def test_area_and_production_end_up_in_one_row():
    clean, failed = run(
        make_row(),
        make_row(element="Area harvested", unit="ha", value="500"),
    )
    assert failed == [] and len(clean) == 1
    assert clean["production_tonnes"].iloc[0] == 1000
    assert clean["area_harvested_ha"].iloc[0] == 500
    assert clean["commodity_group"].iloc[0] == "maize"


def test_negative_value_is_rejected():
    clean, failed = run(make_row(value="-5"))
    assert clean.empty and failed == ["value_range"]


def test_wrong_unit_is_rejected():
    clean, failed = run(make_row(unit="kg"))
    assert clean.empty and failed == ["value_range"]


def test_non_numeric_value_is_rejected():
    clean, failed = run(make_row(value="n/a"))
    assert clean.empty and failed == ["valid_format"]


def test_repeated_crop_element_year_is_rejected():
    clean, failed = run(make_row(), make_row(value="2000"))
    assert failed == ["duplicates"] and len(clean) == 1