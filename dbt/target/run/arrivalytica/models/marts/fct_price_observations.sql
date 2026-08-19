
    

    create  table
      "warehouse"."main"."fct_price_observations__dbt_tmp"
  
    
    as (
      -- Fact table: every clean observation, enriched with the booking-window
-- measure that powers the "when should I buy?" analytics.

with observations as (

    select * from "warehouse"."main"."stg_price_observations"

)

select
    origin,
    destination,
    origin || '-' || destination                    as route,
    price,
    currency,
    depart_date,
    stops,
    stops = 0                                       as is_nonstop,
    found_at,
    is_daily_aggregate,
    first_seen_pull_date,
    -- how far ahead of departure this fare was observed
    depart_date - cast(found_at as date)            as days_before_departure,
    dayname(depart_date)                            as depart_day_of_week
from observations
where depart_date >= cast(found_at as date)  -- guard against stale/odd records
    );
    
  