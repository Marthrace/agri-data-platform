"""Load source CSVs into the raw schema. Safe to run repeatedly."""
import logging

from sqlalchemy import text

from src.extract.read_csv import read_raw_csv
from src.utils.db import get_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("load_raw")

SOURCES = [
    {"path": "data/raw/wfp_food_prices_ghana.csv",
     "table": "wfp_prices", "encoding": "utf-8"},
    {"path": "data/raw/faostat_ghana_crops.csv",
     "table": "faostat_production", "encoding": "utf-8-sig"},
]


def load_source(engine, path, table, encoding):
    df = read_raw_csv(path, encoding)
    source_file = df["_source_file"].iloc[0]

    with engine.begin() as conn:  # one transaction: all or nothing
        # Idempotency: remove rows from an earlier load of this same file
        deleted = conn.execute(
            text(f"DELETE FROM raw.{table} WHERE _source_file = :f"),
            {"f": source_file},
        ).rowcount
        df.to_sql(table, conn, schema="raw", if_exists="append",
                  index=False, method="multi", chunksize=2000)

    log.info("%s: deleted %s old rows, loaded %s rows", table, deleted, len(df))
    return len(df)


def main():
    engine = get_engine()
    for s in SOURCES:
        load_source(engine, s["path"], s["table"], s["encoding"])


if __name__ == "__main__":
    main()