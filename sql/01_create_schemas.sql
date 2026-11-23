-- Layers of the warehouse
CREATE SCHEMA IF NOT EXISTS raw;        -- source data, loaded as received
CREATE SCHEMA IF NOT EXISTS staging;    -- cleaned and validated data
CREATE SCHEMA IF NOT EXISTS analytics;  -- star schema for reporting