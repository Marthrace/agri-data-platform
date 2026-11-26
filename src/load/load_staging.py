"""Clean the raw data and load it into staging.

Default run (incremental): write only the recent window of price data.
Backfill: python -m src.load.load_staging --start 2021-01-01 --end 2021-12-31
"""
import argparse
import datetime as dt
import logging
import uuid

from sqlalchemy import text

from src.load.upsert import upsert
from src.transform.run_cleaning import clean_raw_tables
from src.utils.db import get_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("load_staging")

LOOKBACK_DAYS = 31   # re-check the last month, in case recent prices were corrected
PRICE_KEY = ["price_date", "market", "commodity", "price_type"]
PRODUCTION_KEY = ["commodity_group", "year"]


def incremental_start(latest_loaded):
    """First date to process: a month before the newest price already in staging."""
    if latest_loaded is None:
        return None          # staging is empty, so load everything
    return latest_loaded - dt.timedelta(days=LOOKBACK_DAYS)


def apply_window(prices, production, start, end):
    """Keep only prices dated start..end and production for those years."""
    if start is not None:
        prices = prices[prices["price_date"] >= start]
        production = production[production["year"] >= start.year]
    if end is not None:
        prices = prices[prices["price_date"] <= end]
        production = production[production["year"] <= end.year]
    return prices, production


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Load clean data into staging")
    parser.add_argument("--start", help="backfill from this date (YYYY-MM-DD)")
    parser.add_argument("--end", help="backfill up to this date (YYYY-MM-DD)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    start = dt.date.fromisoformat(args.start) if args.start else None
    end = dt.date.fromisoformat(args.end) if args.end else None
    if start and end and start > end:
        raise SystemExit("--start must not be after --end")
    is_backfill = start is not None or end is not None

    engine = get_engine()
    run_id = uuid.uuid4().hex[:12]

    with engine.begin() as conn:
        if not is_backfill:
            latest = conn.execute(text("SELECT max(price_date) FROM staging.prices")).scalar()
            start = incremental_start(latest)

        prices, production, _, _ = clean_raw_tables(conn, run_id)
        prices, production = apply_window(prices, production, start, end)

        log.info("mode: %s, window: %s to %s",
                 "backfill" if is_backfill else "incremental",
                 start or "start", end or "latest")
        price_result = upsert(conn, prices, "prices", PRICE_KEY)
        production_result = upsert(conn, production, "production", PRODUCTION_KEY)

    log.info("prices:     %s", price_result)
    log.info("production: %s", production_result)


if __name__ == "__main__":
    main()