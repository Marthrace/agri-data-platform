"""Read the raw tables, clean and validate them, and record the results."""
import logging
import uuid

import pandas as pd
from sqlalchemy import text

from src.transform.clean_prices import clean_prices
from src.transform.clean_production import clean_production
from src.utils.db import get_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_cleaning")

LOG_SQL = text(
    "INSERT INTO staging.quality_log "
    "(run_id, dataset, check_name, rows_checked, rows_failed, status) "
    "VALUES (:run_id, :dataset, :check_name, :rows_checked, :rows_failed, :status)"
)
REJECT_SQL = text(
    "INSERT INTO staging.rejected_rows "
    "(run_id, dataset, check_name, reason, row_data) "
    "VALUES (:run_id, :dataset, :check_name, :reason, CAST(:row_data AS JSONB))"
)


def save_results(conn, run_id, checker):
    log_rows = [{"run_id": run_id, "dataset": checker.dataset, **r}
                for r in checker.results]
    if log_rows:
        conn.execute(LOG_SQL, log_rows)
    rejects = [{"run_id": run_id, "dataset": checker.dataset, **r}
               for r in checker.rejected_records()]
    if rejects:
        conn.execute(REJECT_SQL, rejects)


def main():
    engine = get_engine()
    run_id = uuid.uuid4().hex[:12]

    with engine.begin() as conn:
        raw_prices = pd.read_sql(text("SELECT * FROM raw.wfp_prices"), conn)
        raw_production = pd.read_sql(text("SELECT * FROM raw.faostat_production"), conn)

        prices, price_checks = clean_prices(raw_prices)
        production, production_checks = clean_production(raw_production)

        save_results(conn, run_id, price_checks)
        save_results(conn, run_id, production_checks)

    log.info("run %s finished", run_id)
    for checker, clean in [(price_checks, prices), (production_checks, production)]:
        print(f"\n{checker.dataset}: {len(clean)} clean rows")
        print("\n".join(checker.summary_lines()))


if __name__ == "__main__":
    main()