-- Rebuild the star schema from staging. Safe to run repeatedly:
-- every statement inserts new rows and updates changed ones, nothing more.

-- Dates: every day of every year that has prices
INSERT INTO analytics.dim_date (date_key, full_date, year, quarter, month, month_name, year_month)
SELECT to_char(d, 'YYYYMMDD')::INTEGER, d,
       EXTRACT(YEAR FROM d)::INTEGER, EXTRACT(QUARTER FROM d)::INTEGER,
       EXTRACT(MONTH FROM d)::INTEGER, trim(to_char(d, 'Month')), to_char(d, 'YYYY-MM')
FROM (
    SELECT b.first_day + n AS d
    FROM (SELECT make_date(EXTRACT(YEAR FROM min(price_date))::INTEGER, 1, 1) AS first_day,
                 make_date(EXTRACT(YEAR FROM max(price_date))::INTEGER, 12, 31) AS last_day
          FROM staging.prices) AS b,
         generate_series(0, b.last_day - b.first_day) AS n
) AS days
ON CONFLICT (date_key) DO NOTHING;

-- Commodities
INSERT INTO analytics.dim_commodity (commodity_group, commodity_name)
SELECT DISTINCT commodity_group, initcap(commodity_group)
FROM (SELECT commodity_group FROM staging.prices
      UNION
      SELECT commodity_group FROM staging.production) AS c
ON CONFLICT (commodity_group) DO UPDATE SET commodity_name = EXCLUDED.commodity_name;

-- Markets: the most recent description of each market wins
INSERT INTO analytics.dim_market (market_id, market_name, region, district, latitude, longitude)
SELECT DISTINCT ON (market_id) market_id, market, region, district, latitude, longitude
FROM staging.prices
WHERE market_id IS NOT NULL
ORDER BY market_id, price_date DESC
ON CONFLICT (market_id) DO UPDATE
SET market_name = EXCLUDED.market_name, region = EXCLUDED.region,
    district = EXCLUDED.district, latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude;

-- Price facts
INSERT INTO analytics.fact_price
    (date_key, commodity_key, market_key, price_type, price_flag, original_unit,
     kg_per_unit, price_original, price_per_kg_ghs, usd_price_per_kg, data_origin)
SELECT d.date_key, c.commodity_key, m.market_key, p.price_type, p.price_flag,
       p.original_unit, p.kg_per_unit, p.price_original, p.price_per_kg_ghs,
       p.usd_price_per_kg, p.data_origin
FROM staging.prices p
JOIN analytics.dim_date d ON d.full_date = p.price_date
JOIN analytics.dim_commodity c ON c.commodity_group = p.commodity_group
JOIN analytics.dim_market m ON m.market_id = p.market_id
ON CONFLICT (date_key, commodity_key, market_key, price_type) DO UPDATE
SET price_flag = EXCLUDED.price_flag, original_unit = EXCLUDED.original_unit,
    kg_per_unit = EXCLUDED.kg_per_unit, price_original = EXCLUDED.price_original,
    price_per_kg_ghs = EXCLUDED.price_per_kg_ghs,
    usd_price_per_kg = EXCLUDED.usd_price_per_kg,
    data_origin = EXCLUDED.data_origin, _updated_at = now()
WHERE (fact_price.price_flag, fact_price.original_unit, fact_price.kg_per_unit,
       fact_price.price_original, fact_price.price_per_kg_ghs,
       fact_price.usd_price_per_kg, fact_price.data_origin)
      IS DISTINCT FROM
      (EXCLUDED.price_flag, EXCLUDED.original_unit, EXCLUDED.kg_per_unit,
       EXCLUDED.price_original, EXCLUDED.price_per_kg_ghs,
       EXCLUDED.usd_price_per_kg, EXCLUDED.data_origin);

-- Production facts, with yield worked out as tonnes per hectare
INSERT INTO analytics.fact_production
    (commodity_key, year, area_harvested_ha, production_tonnes, yield_t_per_ha, data_origin)
SELECT c.commodity_key, p.year, p.area_harvested_ha, p.production_tonnes,
       round(p.production_tonnes / NULLIF(p.area_harvested_ha, 0), 4), p.data_origin
FROM staging.production p
JOIN analytics.dim_commodity c ON c.commodity_group = p.commodity_group
ON CONFLICT (commodity_key, year) DO UPDATE
SET area_harvested_ha = EXCLUDED.area_harvested_ha,
    production_tonnes = EXCLUDED.production_tonnes,
    yield_t_per_ha = EXCLUDED.yield_t_per_ha,
    data_origin = EXCLUDED.data_origin, _updated_at = now()
WHERE (fact_production.area_harvested_ha, fact_production.production_tonnes,
       fact_production.yield_t_per_ha, fact_production.data_origin)
      IS DISTINCT FROM
      (EXCLUDED.area_harvested_ha, EXCLUDED.production_tonnes,
       EXCLUDED.yield_t_per_ha, EXCLUDED.data_origin);