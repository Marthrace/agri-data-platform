"""Clean and validate raw WFP price rows."""
import re

import pandas as pd

from src.transform.quality import Checker

DATASET = "wfp_prices"
COMMODITY_GROUPS = {
    "Maize": "maize",
    "Rice (local)": "rice",
    "Tomatoes (local)": "tomatoes",
}
START_DATE = "2020-01-01"
REQUIRED = ["date", "admin1", "market", "commodity", "unit",
            "price", "pricetype", "latitude", "longitude"]
MAX_PRICE_PER_KG = 100.0          # GHS; anything above is treated as an error
GHANA_LAT = (4.5, 11.5)           # rough bounding box around Ghana
GHANA_LON = (-3.5, 1.5)


def parse_unit_kg(unit):
    """'KG' -> 1.0, '100 KG' -> 100.0, anything else -> NaN."""
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)?\s*kg\s*", str(unit), flags=re.IGNORECASE)
    if match is None:
        return float("nan")
    return float(match.group(1)) if match.group(1) else 1.0


def clean_prices(raw):
    checker = Checker(DATASET)
    df = raw.copy()

    # Scope: the three project commodities, from START_DATE onward.
    # Rows with an unreadable date stay in so the checks below can reject them.
    df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
    in_scope = df["commodity"].isin(COMMODITY_GROUPS) & (
        (df["date_parsed"] >= START_DATE) | df["date_parsed"].isna()
    )
    checker.info("scope_filter", len(df), (~in_scope).sum())
    df = df[in_scope].copy()

    # Check 1: required fields must not be empty
    text_cols = df[REQUIRED].apply(lambda s: s.fillna("").astype(str).str.strip())
    df = checker.run(df, "not_null", (text_cols == "").any(axis=1),
                     "A required field is empty")

    # Check 2: dates, prices, coordinates and units must be readable
    df["price_num"] = pd.to_numeric(df["price"], errors="coerce")
    df["usdprice_num"] = pd.to_numeric(df["usdprice"], errors="coerce")
    df["lat"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["lon"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["kg_per_unit"] = df["unit"].map(parse_unit_kg)
    unreadable = df[["date_parsed", "price_num", "lat", "lon"]].isna().any(axis=1) \
        | ~(df["kg_per_unit"] > 0)
    df = checker.run(df, "valid_format", unreadable,
                     "Date, price, coordinates or unit could not be read")

    # Check 3: price per kg must be plausible
    df["price_per_kg_ghs"] = df["price_num"] / df["kg_per_unit"]
    implausible = ~df["price_per_kg_ghs"].between(0, MAX_PRICE_PER_KG, inclusive="neither")
    df = checker.run(df, "price_range", implausible,
                     f"Price per kg is not between 0 and {MAX_PRICE_PER_KG} GHS")

    # Check 4: currency must be GHS and the market must sit inside Ghana
    in_ghana = df["lat"].between(*GHANA_LAT) & df["lon"].between(*GHANA_LON)
    wrong_currency = df["currency"].str.strip().str.upper() != "GHS"
    df = checker.run(df, "reference_check", ~in_ghana | wrong_currency,
                     "Currency is not GHS or market is outside Ghana")

    # Check 5: duplicates. If two rows share a key, keep the measured ("actual") one.
    df["_rank"] = (~df["priceflag"].str.contains("actual", na=False)).astype(int)
    df = df.sort_values("_rank", kind="stable")
    key = ["date", "market", "commodity", "pricetype"]
    df = checker.run(df, "duplicates", df.duplicated(key, keep="first"),
                     "Another row has the same date, market, commodity and price type")
    df = df.sort_index()

    clean = pd.DataFrame({
        "price_date": df["date_parsed"].dt.date,
        "region": df["admin1"],
        "district": df["admin2"],
        "market": df["market"],
        "market_id": pd.to_numeric(df["market_id"], errors="coerce").astype("Int64"),
        "latitude": df["lat"],
        "longitude": df["lon"],
        "commodity": df["commodity"],
        "commodity_group": df["commodity"].map(COMMODITY_GROUPS),
        "price_type": df["pricetype"],
        "price_flag": df["priceflag"],
        "original_unit": df["unit"],
        "kg_per_unit": df["kg_per_unit"],
        "price_original": df["price_num"],
        "price_per_kg_ghs": df["price_per_kg_ghs"].round(4),
        "usd_price_per_kg": (df["usdprice_num"] / df["kg_per_unit"]).round(4),
        "currency": df["currency"],
        "data_origin": "real",
        "source_file": df["_source_file"],
    })
    return clean.reset_index(drop=True), checker