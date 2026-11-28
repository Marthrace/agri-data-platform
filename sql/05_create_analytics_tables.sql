-- Star schema for reporting: small dimension tables around two fact tables.
-- Surrogate keys (the *_key columns) are simple whole numbers used for joins.

CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key    INTEGER PRIMARY KEY,           -- 20210615
    full_date   DATE    NOT NULL UNIQUE,
    year        INTEGER NOT NULL,
    quarter     INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    month_name  TEXT    NOT NULL,
    year_month  TEXT    NOT NULL               -- 2021-06
);

CREATE TABLE IF NOT EXISTS analytics.dim_commodity (
    commodity_key    SERIAL PRIMARY KEY,
    commodity_group  TEXT NOT NULL UNIQUE,     -- maize, rice, tomatoes
    commodity_name   TEXT NOT NULL             -- Maize, Rice, Tomatoes
);

CREATE TABLE IF NOT EXISTS analytics.dim_market (
    market_key   SERIAL PRIMARY KEY,
    market_id    INTEGER NOT NULL UNIQUE,      -- WFP's own market id
    market_name  TEXT    NOT NULL,
    region       TEXT,
    district     TEXT,
    latitude     NUMERIC(9,6),
    longitude    NUMERIC(9,6)
);

-- Grain: one row per commodity, per market, per date, per price type
CREATE TABLE IF NOT EXISTS analytics.fact_price (
    date_key          INTEGER NOT NULL REFERENCES analytics.dim_date (date_key),
    commodity_key     INTEGER NOT NULL REFERENCES analytics.dim_commodity (commodity_key),
    market_key        INTEGER NOT NULL REFERENCES analytics.dim_market (market_key),
    price_type        TEXT    NOT NULL,        -- Retail or Wholesale
    price_flag        TEXT,
    original_unit     TEXT,
    kg_per_unit       NUMERIC,
    price_original    NUMERIC,
    price_per_kg_ghs  NUMERIC(12,4),
    usd_price_per_kg  NUMERIC(12,4),
    data_origin       TEXT    NOT NULL,
    _loaded_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    _updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (date_key, commodity_key, market_key, price_type)
);

-- Grain: one row per commodity per year
CREATE TABLE IF NOT EXISTS analytics.fact_production (
    commodity_key      INTEGER NOT NULL REFERENCES analytics.dim_commodity (commodity_key),
    year               INTEGER NOT NULL,
    area_harvested_ha  NUMERIC,
    production_tonnes  NUMERIC,
    yield_t_per_ha     NUMERIC(12,4),
    data_origin        TEXT NOT NULL,
    _loaded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    _updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (commodity_key, year)
);

-- A flat, readable view for quick questions and for dashboards
CREATE OR REPLACE VIEW analytics.v_prices AS
SELECT d.full_date, d.year, d.month, d.year_month,
       c.commodity_name, m.market_name, m.region, m.latitude, m.longitude,
       f.price_type, f.price_per_kg_ghs, f.usd_price_per_kg
FROM analytics.fact_price f
JOIN analytics.dim_date d ON d.date_key = f.date_key
JOIN analytics.dim_commodity c ON c.commodity_key = f.commodity_key
JOIN analytics.dim_market m ON m.market_key = f.market_key;

-- One row per pipeline run
CREATE TABLE IF NOT EXISTS staging.run_log (
    id           BIGSERIAL PRIMARY KEY,
    run_id       TEXT NOT NULL UNIQUE,
    pipeline     TEXT NOT NULL,
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at  TIMESTAMPTZ,
    status       TEXT NOT NULL,                -- running, success or failed
    details      JSONB,
    error        TEXT
);