-- Results of every validation check, one row per check per run
CREATE TABLE IF NOT EXISTS staging.quality_log (
    id            BIGSERIAL PRIMARY KEY,
    run_id        TEXT NOT NULL,
    run_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    dataset       TEXT NOT NULL,
    check_name    TEXT NOT NULL,
    rows_checked  INTEGER NOT NULL,
    rows_failed   INTEGER NOT NULL,
    status        TEXT NOT NULL      -- pass, fail or info
);

-- Rows that failed a check, kept so nothing disappears silently
CREATE TABLE IF NOT EXISTS staging.rejected_rows (
    id           BIGSERIAL PRIMARY KEY,
    run_id       TEXT NOT NULL,
    rejected_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    dataset      TEXT NOT NULL,
    check_name   TEXT NOT NULL,
    reason       TEXT NOT NULL,
    row_data     JSONB NOT NULL      -- the whole original row
);