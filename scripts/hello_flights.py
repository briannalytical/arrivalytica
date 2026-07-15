"""Phase 0 smoke test: verify the Travelpayouts token and fetch one route.

Usage:
    1. Ensure .env contains TRAVELPAYOUTS_TOKEN=<your token>
    2. pip install -e .
    3. python scripts/hello_flights.py
"""

from pathlib import Path

import yaml
from dotenv import load_dotenv

from flight_tracker.travelpayouts_client import TravelpayoutsClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    config = yaml.safe_load((PROJECT_ROOT / "config" / "routes.yaml").read_text())
    route = config["routes"][0]
    currency = config["settings"]["currency"].lower()

    print(f"Fetching latest observed prices: {route['origin']} -> {route['destination']} ...")

    client = TravelpayoutsClient()
    try:
        result = client.latest_prices(
            origin=route["origin"],
            destination=route["destination"],
            currency=currency,
            limit=10,
        )
    finally:
        client.close()

    observations = result.get("data", [])
    if not observations:
        print("Token works (no auth error), but no cached prices for this route right now.")
        print("Try another route — popularity affects cache coverage.")
        return

    print(f"\nGot {len(observations)} price observations. Cheapest first:\n")
    for obs in observations[:10]:
        print(
            f"  {obs.get('value'):>8} {currency.upper()}"
            f"  | depart {obs.get('depart_date')}"
            f"  | {obs.get('number_of_changes', '?')} stop(s)"
            f"  | seen {obs.get('found_at')}"
        )

    print("\nToken verified against the live API. Phase 0 complete — commit and move to Phase 1.")


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
