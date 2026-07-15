"""Phase 0 smoke test: verify Amadeus credentials and fetch one route.

Usage:
    1. Copy .env.example to .env and fill in your Amadeus keys
    2. pip install -e .
    3. python scripts/hello_flights.py
"""

from datetime import date, timedelta
from pathlib import Path

import yaml
from dotenv import load_dotenv

from flight_tracker.amadeus_client import AmadeusClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    config = yaml.safe_load((PROJECT_ROOT / "config" / "routes.yaml").read_text())
    route = config["routes"][0]
    settings = config["settings"]

    departure = date.today() + timedelta(days=30)

    print(f"Searching {route['origin']} -> {route['destination']} on {departure} ...")

    client = AmadeusClient()
    try:
        result = client.search_flight_offers(
            origin=route["origin"],
            destination=route["destination"],
            departure_date=departure.isoformat(),
            adults=settings["adults"],
            currency=settings["currency"],
            max_results=5,
        )
    finally:
        client.close()

    offers = result.get("data", [])
    if not offers:
        print("No offers returned. (Test environment coverage is spotty —")
        print(" try a different date or route before assuming something is broken.)")
        return

    print(f"\nGot {len(offers)} offers. Cheapest options:\n")
    for offer in sorted(offers, key=lambda o: float(o["price"]["grandTotal"])):
        price = offer["price"]
        first_itin = offer["itineraries"][0]
        stops = len(first_itin["segments"]) - 1
        carrier = first_itin["segments"][0]["carrierCode"]
        print(
            f"  {price['grandTotal']} {price['currency']}"
            f"  | carrier {carrier} | {stops} stop(s)"
            f"  | duration {first_itin['duration']}"
        )

    print("\nCredentials work. Phase 0 complete — commit and move to Phase 1.")


if __name__ == "__main__":
    main()
