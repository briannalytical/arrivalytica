"""Phase 1 ingestion: pull latest observed prices for all configured routes
and write them to the bronze Parquet layer.

Design decisions (see README):
- One partition per pull date: data/bronze/latest_prices/pull_date=YYYY-MM-DD/
- Idempotent: re-running today overwrites today's partition file cleanly.
- Per-route fault tolerance: one failing route logs a warning; the run continues.
- Bronze = faithful capture: a few core fields are promoted to typed columns
  for convenience, and the COMPLETE raw record is preserved in `raw_json`.
  All real cleaning/typing happens downstream in dbt.
- Every run writes a _manifest.json: when it ran, per-route record counts,
  and any failures. Future-you debugging a data gap will be grateful.

Run from the project root:
    python -m flight_tracker.extract
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from dotenv import load_dotenv

from flight_tracker.travelpayouts_client import TravelpayoutsClient, TravelpayoutsError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze" / "latest_prices"

# Promoted columns: explicitly typed so the Parquet schema is stable
# run-to-run even if the API adds/removes fields.
SCHEMA = pa.schema(
    [
        ("origin_requested", pa.string()),
        ("destination_requested", pa.string()),
        ("value", pa.float64()),
        ("currency", pa.string()),
        ("depart_date", pa.string()),
        ("return_date", pa.string()),
        ("number_of_changes", pa.int32()),
        ("found_at", pa.string()),
        ("distance", pa.int64()),
        ("raw_json", pa.string()),
        ("pulled_at_utc", pa.string()),
        ("pull_date", pa.string()),
    ]
)


def extract_route(
    client: TravelpayoutsClient,
    origin: str,
    destination: str,
    currency: str,
    pull_date: str,
    pulled_at: str,
) -> list[dict]:
    """Fetch latest prices for one route and shape records for the bronze layer."""
    payload = client.latest_prices(
        origin=origin,
        destination=destination,
        currency=currency,
        limit=1000,
    )
    records = payload.get("data", []) or []

    rows = []
    for rec in records:
        rows.append(
            {
                "origin_requested": origin,
                "destination_requested": destination,
                "value": float(rec["value"]) if rec.get("value") is not None else None,
                "currency": currency,
                "depart_date": rec.get("depart_date"),
                "return_date": rec.get("return_date"),
                "number_of_changes": rec.get("number_of_changes"),
                "found_at": rec.get("found_at"),
                "distance": rec.get("distance"),
                "raw_json": json.dumps(rec, ensure_ascii=False),
                "pulled_at_utc": pulled_at,
                "pull_date": pull_date,
            }
        )
    return rows


def write_partition(rows: list[dict], pull_date: str) -> Path:
    """Write all rows for this pull to a single partition, overwriting any
    previous file for the same pull_date (idempotency)."""
    partition_dir = BRONZE_DIR / f"pull_date={pull_date}"
    partition_dir.mkdir(parents=True, exist_ok=True)
    out_path = partition_dir / "data.parquet"

    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    pq.write_table(table, out_path)  # write_table overwrites by default
    return out_path


def write_manifest(
    pull_date: str,
    started_at: str,
    route_counts: dict[str, int],
    failures: dict[str, str],
) -> Path:
    partition_dir = BRONZE_DIR / f"pull_date={pull_date}"
    partition_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = partition_dir / "_manifest.json"
    manifest = {
        "pull_date": pull_date,
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "routes_attempted": len(route_counts) + len(failures),
        "routes_succeeded": len(route_counts),
        "records_per_route": route_counts,
        "failures": failures,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest_path


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    config = yaml.safe_load((PROJECT_ROOT / "config" / "routes.yaml").read_text())
    routes = config["routes"]
    currency = config["settings"]["currency"].lower()

    pull_date = date.today().isoformat()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    all_rows: list[dict] = []
    route_counts: dict[str, int] = {}
    failures: dict[str, str] = {}

    client = TravelpayoutsClient()
    try:
        for route in routes:
            key = f"{route['origin']}-{route['destination']}"
            try:
                rows = extract_route(
                    client,
                    origin=route["origin"],
                    destination=route["destination"],
                    currency=currency,
                    pull_date=pull_date,
                    pulled_at=started_at,
                )
                route_counts[key] = len(rows)
                all_rows.extend(rows)
                print(f"  {key}: {len(rows)} records")
            except TravelpayoutsError as exc:
                failures[key] = str(exc)
                print(f"  {key}: FAILED — {exc}", file=sys.stderr)
    finally:
        client.close()

    if not route_counts:
        print("All routes failed — nothing written.", file=sys.stderr)
        write_manifest(pull_date, started_at, route_counts, failures)
        return 1

    out_path = write_partition(all_rows, pull_date)
    manifest_path = write_manifest(pull_date, started_at, route_counts, failures)

    print(f"\nWrote {len(all_rows)} records -> {out_path.relative_to(PROJECT_ROOT)}")
    print(f"Manifest -> {manifest_path.relative_to(PROJECT_ROOT)}")
    if failures:
        print(f"NOTE: {len(failures)} route(s) failed this run — see manifest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
