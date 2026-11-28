"""Run the whole pipeline: raw load, cleaning and staging, then the star schema.

    python -m src.run_pipeline
    python -m src.run_pipeline --start 2021-01-01 --end 2021-12-31    (backfill)
"""
import argparse
import json
import logging
import time
import uuid

from sqlalchemy import text

from src.load import load_raw, load_staging
from src.load.build_star import build_star
from src.utils.db import get_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pipeline")

COUNTED_TABLES = [
    "raw.wfp_prices", "raw.faostat_production",
    "staging.prices", "staging.production", "staging.rejected_rows",
    "analytics.dim_date", "analytics.dim_commodity", "analytics.dim_market",
    "analytics.fact_price", "analytics.fact_production",
]


def run_with_retries(func, retries=2, delay=5, sleep=time.sleep):
    """Call func. If it raises, wait and try again, up to `retries` more times."""
    for attempt in range(1, retries + 2):
        try:
            return func()
        except Exception as exc:
            if attempt > retries:
                raise
            log.warning("attempt %s failed (%s); retrying in %ss", attempt, exc, delay)
            sleep(delay)


def start_run(engine, run_id):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO staging.run_log (run_id, pipeline, status) "
                 "VALUES (:run_id, 'daily', 'running')"),
            {"run_id": run_id},
        )


def finish_run(engine, run_id, status, details, error=None):
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE staging.run_log SET finished_at = now(), status = :status, "
                 "details = CAST(:details AS JSONB), error = :error WHERE run_id = :run_id"),
            {"run_id": run_id, "status": status,
             "details": json.dumps(details), "error": error},
        )


def table_counts(engine):
    with engine.connect() as conn:
        return {t: conn.execute(text(f"SELECT count(*) FROM {t}")).scalar()
                for t in COUNTED_TABLES}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run the full pipeline")
    parser.add_argument("--start", help="backfill from this date (YYYY-MM-DD)")
    parser.add_argument("--end", help="backfill up to this date (YYYY-MM-DD)")
    parser.add_argument("--retries", type=int, default=2, help="extra attempts per step")
    parser.add_argument("--delay", type=int, default=5, help="seconds between attempts")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    staging_args = []
    if args.start:
        staging_args += ["--start", args.start]
    if args.end:
        staging_args += ["--end", args.end]

    def build_analytics():
        with get_engine().begin() as conn:
            build_star(conn)

    steps = [
        ("load_raw", load_raw.main),
        ("load_staging", lambda: load_staging.main(staging_args)),
        ("build_analytics", build_analytics),
    ]

    engine = get_engine()
    run_id = uuid.uuid4().hex[:12]
    start_run(engine, run_id)
    log.info("pipeline run %s started", run_id)

    timings = {}
    current = None
    try:
        for current, func in steps:
            began = time.time()
            run_with_retries(func, args.retries, args.delay)
            timings[current] = round(time.time() - began, 1)
            log.info("step %s done in %ss", current, timings[current])
    except Exception as exc:
        log.error("pipeline run %s FAILED at step %s: %s", run_id, current, exc)
        finish_run(engine, run_id, "failed",
                   {"failed_step": current, "timings": timings}, str(exc)[:2000])
        raise SystemExit(1)

    counts = table_counts(engine)
    finish_run(engine, run_id, "success", {"timings": timings, "row_counts": counts})
    log.info("pipeline run %s succeeded", run_id)
    for table, n in counts.items():
        print(f"  {table:<28} {n:>7}")


if __name__ == "__main__":
    main()