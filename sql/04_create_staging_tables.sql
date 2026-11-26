-- Staging layer: cleaned, typed data. The primary key is the natural key,
-- which is what lets a rerun update a row instead of duplicating it.

CREATE TABLE IF NOT EXISTS staging.prices (
    price_date        DATE          NOT NULL,
    region            TEXT,
    district          TEXT,
    market            TEXT          NOT NULL,
    market_id         INTEGER,
    latitude          NUMERIC(9,6),
    longitude         NUMERIC(9,6),
    commodity         TEXT          NOT NULL,
    commodity_group   TEXT          NOT NULL,
    price_type        TEXT          NOT NULL,
    price_flag        TEXT,
    original_unit     TEXT,
    kg_per_unit       NUMERIC,
    price_original    NUMERIC,
    price_per_kg_ghs  NUMERIC(12,4),
    usd_price_per_kg  NUMERIC(12,4),
    currency          TEXT,
    data_origin       TEXT          NOT NULL,
    source_file       TEXT,
    _loaded_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),
    _updated_at       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    PRIMARY KEY (price_date, market, commodity, price_type)
);

CREATE TABLE IF NOT EXISTS staging.production (
    commodity_group    TEXT         NOT NULL,
    year               INTEGER      NOT NULL,
    area_harvested_ha  NUMERIC,
    production_tonnes  NUMERIC,
    data_origin        TEXT         NOT NULL,
    source_file        TEXT,
    _loaded_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    _updated_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    PRIMARY KEY (commodity_group, year)
);