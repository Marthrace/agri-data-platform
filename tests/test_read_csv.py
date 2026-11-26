from src.extract.read_csv import clean_column_name, read_raw_csv


def test_clean_column_name_handles_spaces_and_brackets():
    assert clean_column_name("Area Code (M49)") == "area_code_m49"


def test_clean_column_name_lowercases():
    assert clean_column_name("Item") == "item"


def test_read_raw_csv_keeps_leading_zeros_and_adds_source(tmp_path):
    f = tmp_path / "sample.csv"
    f.write_text("Item Code (CPC),Value\n0112,5\n", encoding="utf-8")
    df = read_raw_csv(f)
    assert df["item_code_cpc"].iloc[0] == "0112"
    assert df["_source_file"].iloc[0] == "sample.csv"