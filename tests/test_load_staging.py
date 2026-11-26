import datetime as dt

import pandas as pd

from src.load.load_staging import apply_window, incremental_start


def sample_frames():
    prices = pd.DataFrame({"price_date": [dt.date(2020, 5, 15), dt.date(2021, 6, 15),
                                          dt.date(2022, 7, 15)]})
    production = pd.DataFrame({"year": [2020, 2021, 2022]})
    return prices, production


def test_incremental_start_is_none_when_staging_is_empty():
    assert incremental_start(None) is None


def test_incremental_start_looks_back_one_month():
    assert incremental_start(dt.date(2023, 7, 15)) == dt.date(2023, 6, 14)


def test_apply_window_with_no_dates_keeps_everything():
    prices, production = sample_frames()
    p, q = apply_window(prices, production, None, None)
    assert len(p) == 3 and len(q) == 3


def test_apply_window_filters_prices_by_date_and_production_by_year():
    prices, production = sample_frames()
    p, q = apply_window(prices, production, dt.date(2021, 1, 1), dt.date(2021, 12, 31))
    assert list(p["price_date"]) == [dt.date(2021, 6, 15)]
    assert list(q["year"]) == [2021]


def test_apply_window_start_only_keeps_later_rows():
    prices, production = sample_frames()
    p, q = apply_window(prices, production, dt.date(2021, 1, 1), None)
    assert len(p) == 2 and list(q["year"]) == [2021, 2022]