# Flight Price Tracker

An end-to-end data engineering pipeline that tracks international flight
prices over time and answers questions like *"how far in advance should I
book?"* and *"which day of the week is cheapest to fly?"*

## Architecture (planned)

Amadeus API -> Python ingestion -> Parquet (bronze) -> dbt + DuckDB (silver/gold) -> Streamlit dashboard
                     ^
                Airflow orchestration, Docker Compose, GitHub Actions CI

## Status

- [x] Phase 0 — repo scaffold + API smoke test
- [ ] Phase 1 — scheduled ingestion to partitioned Parquet
- [ ] Phase 2 — dbt models + data quality tests
- [ ] Phase 3 — Airflow orchestration
- [ ] Phase 4 — Streamlit dashboard + price-drop alerts
- [ ] Phase 5 — CI, architecture docs, polish

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # fill in keys
python scripts/hello_flights.py
```


### [Update 8/18/26] 
## Running the pipeline

From the project root, with the venv active:

    source .venv/bin/activate

**1. Extract** — pull all configured routes into today's bronze partition:

    python3 -m flight_tracker.extract

**2. Transform + test** — rebuild the dbt models and run data quality tests:

    cd dbt && dbt build --profiles-dir . && cd ..

Other commands:

    python3 scripts/get_flights.py                      # API smoke test (token check)
    python3 scripts/query.py queries/route_summary.sql  # run an exploratory query
