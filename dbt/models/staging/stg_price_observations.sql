-- Staging: one clean, typed row per unique price observation.
--
-- Cleaning applied here (and only here — marts trust this model):
--   * Cast strings to real DATE/TIMESTAMP/numeric types.
--   * Flag daily-aggregate records: the API mixes individually observed
--     fares (real timestamps) with daily aggregates (found_at stamped
--     exactly midnight). Discovered during Phase 0 smoke testing.
--   * Deduplicate: the same cached observation can be captured by
--     multiple daily pulls; keep one row per unique observation,
--     remembering the first pull that saw it.

with source as (

    select * from {{ source('bronze', 'latest_prices') }}

),

typed as (

    select
        origin_requested                          as origin,
        destination_requested                     as destination,
        cast(value as double)                     as price,
        upper(currency)                           as currency,
        cast(depart_date as date)                 as depart_date,
        cast(return_date as date)                 as return_date,
        cast(number_of_changes as integer)        as stops,
        cast(found_at as timestamp)               as found_at,
        cast(distance as integer)                 as distance_km,
        cast(pull_date as date)                   as pull_date,
        cast(pulled_at_utc as timestamp)          as pulled_at_utc,
        raw_json
    from source

),

flagged as (

    select
        *,
        -- midnight-stamped found_at = daily aggregate, not a discrete observation
        (extract(hour from found_at) = 0
         and extract(minute from found_at) = 0
         and extract(second from found_at) = 0)   as is_daily_aggregate
    from typed

),

deduped as (

    select
        *,
        row_number() over (
            partition by origin, destination, depart_date, found_at, price, stops
            order by pull_date
        ) as _rn
    from flagged

)

select
    origin,
    destination,
    price,
    currency,
    depart_date,
    return_date,
    stops,
    found_at,
    is_daily_aggregate,
    distance_km,
    pull_date as first_seen_pull_date,
    pulled_at_utc,
    raw_json
from deduped
where _rn = 1
