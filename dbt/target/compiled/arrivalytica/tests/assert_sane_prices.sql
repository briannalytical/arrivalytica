-- Fails if any observation has a non-positive or absurd price.
-- (A $0 or $90,000 economy fare is a data quality problem, not a deal.)

select *
from "warehouse"."main"."stg_price_observations"
where price <= 0
   or price > 20000