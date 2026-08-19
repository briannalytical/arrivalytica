
    

    create  table
      "warehouse"."main"."route_daily_summary__dbt_tmp"
  
    
    as (
      -- One row per route per pull date: the daily pulse of each route.
-- This is the table the dashboard's trend lines will read.

with observations as (

    select * from "warehouse"."main"."stg_price_observations"

)

select
    origin,
    destination,
    origin || '-' || destination        as route,
    first_seen_pull_date                as pull_date,
    count(*)                            as observations,
    min(price)                          as min_price,
    round(avg(price), 2)                as avg_price,
    max(price)                          as max_price,
    round(stddev_samp(price), 2)        as price_stddev,
    min(price) filter (stops = 0)       as min_price_nonstop,
    count(*)  filter (stops = 0)        as nonstop_observations
from observations
group by 1, 2, 3, 4
    );
    
  