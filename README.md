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
cp .env.example .env   # then fill in your Amadeus keys
python scripts/hello_flights.py
```

## Design decisions

(Documented as the project evolves — see commits.)
