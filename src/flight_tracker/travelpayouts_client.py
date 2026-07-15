"""Travelpayouts (Aviasales) Data API client.

Replaces the original Amadeus client after Amadeus decommissioned its
self-service portal (July 2026). See README "Design decisions."

The Data API serves *cached* market prices — fares recently observed in
real user searches — rather than live shopping quotes. For trend
analytics this is ideal: it reflects what the market actually offered.

Auth is a single token passed via the X-Access-Token header.
No OAuth dance required (one of several ways this API is simpler
than Amadeus was).
"""

from __future__ import annotations

import os

import httpx

BASE_URL = "https://api.travelpayouts.com"


class TravelpayoutsError(RuntimeError):
    """Raised when the Travelpayouts API returns an error response."""


class TravelpayoutsClient:
    def __init__(self, token: str | None = None, base_url: str = BASE_URL) -> None:
        self.token = token or os.environ["TRAVELPAYOUTS_TOKEN"]
        self.base_url = base_url
        self._http = httpx.Client(
            timeout=30,
            headers={"X-Access-Token": self.token},
        )

    def _get(self, path: str, params: dict) -> dict:
        resp = self._http.get(f"{self.base_url}{path}", params=params)
        if resp.status_code != 200:
            raise TravelpayoutsError(
                f"GET {path} failed ({resp.status_code}): {resp.text[:300]}"
            )
        payload = resp.json()
        if payload.get("success") is False:
            raise TravelpayoutsError(f"GET {path} returned success=false: {payload}")
        return payload

    # --- endpoints ------------------------------------------------------

    def latest_prices(
        self,
        origin: str,
        destination: str,
        currency: str = "usd",
        one_way: bool = True,
        period_type: str = "year",
        limit: int = 100,
        page: int = 1,
    ) -> dict:
        """Prices observed in user searches over the last ~48 hours.

        Rich per-observation records (price, depart_date, found_at,
        number_of_changes/stops, distance). This is the primary
        ingestion endpoint: polled on a schedule, it builds our
        price-over-time history.
        """
        return self._get(
            "/v2/prices/latest",
            {
                "origin": origin,
                "destination": destination,
                "currency": currency,
                "one_way": str(one_way).lower(),
                "period_type": period_type,
                "limit": limit,
                "page": page,
                "sorting": "price",
            },
        )

    def cheapest_tickets(
        self,
        origin: str,
        destination: str,
        depart_date: str | None = None,  # YYYY-MM or YYYY-MM-DD
        return_date: str | None = None,
        currency: str = "usd",
    ) -> dict:
        """Cheapest cached tickets for a route, optionally filtered by month/date."""
        params: dict = {
            "origin": origin,
            "destination": destination,
            "currency": currency,
        }
        if depart_date:
            params["depart_date"] = depart_date
        if return_date:
            params["return_date"] = return_date
        return self._get("/v1/prices/cheap", params)

    def month_matrix(
        self,
        origin: str,
        destination: str,
        month: str,  # YYYY-MM-01
        currency: str = "usd",
    ) -> dict:
        """Calendar of cheapest prices for each day of a month.

        Useful for the day-of-week and booking-window analytics.
        """
        return self._get(
            "/v2/prices/month-matrix",
            {
                "origin": origin,
                "destination": destination,
                "month": month,
                "currency": currency,
                "show_to_affiliates": "false",
            },
        )

    def close(self) -> None:
        self._http.close()
