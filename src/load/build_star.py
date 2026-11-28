"""Build the analytics star schema from staging, then check the row counts."""
import logging
from pathlib import Path

from sqlalchemy import text

from src.utils.db import get_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("build_star")

SQL_FILE = Path(__file__).resolve().parents[2] / "sql" / "06_build_analytics.sql"

# Every staging row must have landed in a fact table. A mismatch means rows
# were lost in a join, so the run must fail loudly instead of passing quietly.
RECONCILIATION = [
    ("fact_price", "SELECT (SELECT count(*) FROM analytics.fact_price), "
                   "(SELECT count(*) FROM staging.prices)"),
    ("fact_production", "SELECT (SELECT count(*) FROM analytics.fact_production), "
                        "(SELECT count(*) FROM staging.production)"),
]


def build_star(conn):
    conn.exec_driver_sql(SQL_FILE.read_text(encoding="utf-8-sig"))
    for name, sql in RECONCILIATION:
        in_star, in_staging = conn.execute(text(sql)).one()
        if in_star != in_staging:
            raise RuntimeError(f"{name} has {in_star} rows but staging has {in_staging}")
        log.info("%s reconciles with staging: %s rows", name, in_star)


def main():
    with get_engine().begin() as conn:
        build_star(conn)


if __name__ == "__main__":
    main()