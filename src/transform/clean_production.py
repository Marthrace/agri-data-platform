"""Clean and validate raw FAOSTAT production rows."""
import pandas as pd

from src.transform.quality import Checker

DATASET = "faostat_production"
ITEM_GROUPS = {"Maize (corn)": "maize", "Rice": "rice", "Tomatoes": "tomatoes"}
# element name -> (output column, expected unit)
ELEMENTS = {
    "Area harvested": ("area_harvested_ha", "ha"),
    "Production": ("production_tonnes", "t"),
}
REQUIRED = ["item", "element", "year", "value", "unit"]


def clean_production(raw):
    checker = Checker(DATASET)
    df = raw.copy()

    in_scope = df["item"].isin(ITEM_GROUPS) & df["element"].isin(ELEMENTS)
    checker.info("scope_filter", len(df), (~in_scope).sum())
    df = df[in_scope].copy()

    # Check 1: required fields must not be empty
    text_cols = df[REQUIRED].apply(lambda s: s.fillna("").astype(str).str.strip())
    df = checker.run(df, "not_null", (text_cols == "").any(axis=1),
                     "A required field is empty")

    # Check 2: year and value must be numbers
    df["year_num"] = pd.to_numeric(df["year"], errors="coerce")
    df["value_num"] = pd.to_numeric(df["value"], errors="coerce")
    df = checker.run(df, "valid_format",
                     df[["year_num", "value_num"]].isna().any(axis=1),
                     "Year or value could not be read")

    # Check 3: values cannot be negative and units must match the element
    expected_unit = df["element"].map(lambda e: ELEMENTS[e][1])
    bad = (df["value_num"] < 0) | (df["unit"].str.strip() != expected_unit)
    df = checker.run(df, "value_range", bad,
                     "Value is negative or the unit is not the expected one")

    # Check 4: no repeated crop, element and year
    df = checker.run(df, "duplicates",
                     df.duplicated(["item", "element", "year_num"], keep="first"),
                     "Another row has the same crop, element and year")

    # Reshape: one row per crop and year, area and production side by side
    df["commodity_group"] = df["item"].map(ITEM_GROUPS)
    df["measure"] = df["element"].map(lambda e: ELEMENTS[e][0])
    wide = df.pivot(index=["commodity_group", "year_num"],
                    columns="measure", values="value_num").reset_index()
    for column, _ in ELEMENTS.values():
        if column not in wide.columns:
            wide[column] = float("nan")

    clean = pd.DataFrame({
        "commodity_group": wide["commodity_group"],
        "year": wide["year_num"].astype(int),
        "area_harvested_ha": wide["area_harvested_ha"],
        "production_tonnes": wide["production_tonnes"],
        "data_origin": "real",
        "source_file": df["_source_file"].iloc[0] if len(df) else "",
    })
    return clean, checker