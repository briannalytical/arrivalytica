-- split_ticket_opportunities.sql
-- ------------------------------------------------------------------
-- Question: for a given through-route, would two separate tickets
-- via a positioning hub have been cheaper than the through-fare?
--
-- Compares the cheapest observed through-fare per departure date
-- against cheapest(leg1 into hub) + cheapest(leg2 out of hub),
-- allowing same-day connections or one overnight at the hub.
--
-- KNOWN NAIVETIES (see README design decisions):
--   * Legs are cheapest fares observed independently — the sum is an
--     opportunity signal, not a bookable quote.
--   * Separate tickets carry real risks the data can't see: no
--     missed-connection protection, bag re-check, airport-change
--     hassle at multi-airport cities (e.g. LGW vs STN).
--   * Prices come from cached observations at different moments.
--
-- Edit the three parameters marked <-- below, then run:
--   python3 scripts/query.py queries/split_ticket_opportunities.sql
--
-- In Phase 2 this becomes a dbt model with the hub list as a seed
-- table instead of a hardcoded IN clause.
-- ------------------------------------------------------------------

WITH observations AS (
    SELECT origin_requested AS origin,
           destination_requested AS dest,
           depart_date,
           value
    FROM 'data/bronze/latest_prices/pull_date=*/data.parquet'
),

-- cheapest observed fare per route per departure date
cheapest AS (
    SELECT origin, dest, depart_date, MIN(value) AS min_price
    FROM observations
    GROUP BY 1, 2, 3
),

-- the through-fares we want to beat
through_fares AS (
    SELECT * FROM cheapest
    WHERE origin = 'DTW'                             -- <-- through-route origin
      AND dest   = 'LHR'                             -- <-- through-route destination
),

-- leg1 + leg2 via each candidate hub;
-- leg2 departs same day as leg1 or the next day (overnight at hub)
split_tickets AS (
    SELECT l1.origin,
           l2.dest,
           l1.depart_date,                           -- trip start date
           l1.dest AS via_hub,
           CAST(l2.depart_date AS DATE)
             - CAST(l1.depart_date AS DATE)          AS overnight_days,
           l1.min_price                              AS leg1_price,
           l2.min_price                              AS leg2_price,
           l1.min_price + l2.min_price               AS split_total
    FROM cheapest l1
    JOIN cheapest l2
      ON l2.origin = l1.dest                         -- leg2 starts where leg1 lands
     AND CAST(l2.depart_date AS DATE)
         BETWEEN CAST(l1.depart_date AS DATE)        -- same day...
             AND CAST(l1.depart_date AS DATE) + 1    -- ...or next morning
    WHERE l1.origin = 'DTW'                          -- <-- match through-route origin
      AND l2.dest   = 'LHR'                          -- <-- match through-route destination
      AND l1.dest IN (                               -- <-- candidate positioning hubs
          'KEF','DUB','LIS','LGW',                   --     transatlantic
          'ICN','TPE','NRT',                         --     transpacific
          'MEX','BOG','LIM','FLL'                    --     latin america
      )
)

SELECT t.depart_date,
       s.via_hub,
       s.overnight_days,
       t.min_price                 AS through_fare,
       s.leg1_price,
       s.leg2_price,
       s.split_total,
       t.min_price - s.split_total AS savings
FROM through_fares t
JOIN split_tickets s
  ON s.depart_date = t.depart_date
ORDER BY savings DESC;
