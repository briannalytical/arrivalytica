-- route_summary.sql
-- ------------------------------------------------------------------
-- Question: across everything collected so far, what does each
-- route's price landscape look like?
--
-- Cheapest / average / spread per route, plus observation counts
-- (low counts = thin cache coverage = noisier stats).
--
-- Run from the project root:
--   python3 scripts/query.py queries/route_summary.sql
-- ------------------------------------------------------------------

SELECT origin_requested        AS origin,
       destination_requested   AS dest,
       COUNT(*)                AS observations,
       COUNT(DISTINCT pull_date) AS days_collected,
       MIN(value)              AS cheapest,
       ROUND(AVG(value))       AS avg_price,
       MAX(value)              AS priciest
FROM 'data/bronze/latest_prices/pull_date=*/data.parquet'
GROUP BY 1, 2
ORDER BY cheapest;
