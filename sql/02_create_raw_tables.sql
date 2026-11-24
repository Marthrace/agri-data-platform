-- Raw layer: every source column stored as TEXT, exactly as received.
-- Two metadata columns record where and when each row was loaded.

CREATE TABLE IF NOT EXISTS raw.wfp_prices (
    date          TEXT,
    admin1        TEXT,
    admin2        TEXT,
    market        TEXT,
    market_id     TEXT,
    latitude      TEXT,
    longitude     TEXT,
    category      TEXT,
    commodity     TEXT,
    commodity_id  TEXT,
    unit          TEXT,
    priceflag     TEXT,
    pricetype     TEXT,
    currency      TEXT,
    price         TEXT,
    usdprice      TEXT,
    _source_file  TEXT NOT NULL,
    _loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.faostat_production (
    domain_code      TEXT,
    domain           TEXT,
    area_code_m49    TEXT,
    area             TEXT,
    element_code     TEXT,
    element          TEXT,
    item_code_cpc    TEXT,
    item             TEXT,
    year_code        TEXT,
    year             TEXT,
    unit             TEXT,
    value            TEXT,
    flag             TEXT,
    flag_description TEXT,
    note             TEXT,
    _source_file     TEXT NOT NULL,
    _loaded_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);