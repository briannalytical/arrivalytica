"""Minimal Amadeus Self-Service API client.

Handles OAuth2 token acquisition/refresh and flight offer searches
against the TEST environment. Phase 1 will add retries, rate-limit
handling, and pagination.
"""

from __future__ import annotations

import os
import time

import httpx

TEST_BASE_URL = "https://test.api.amadeus.com"


class AmadeusError(RuntimeError):
    """Raised when the Amadeus API returns an error response."""


class AmadeusClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        base_url: str = TEST_BASE_URL,
    ) -> None:
        self.client_id = client_id or os.environ["AMADEUS_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["AMADEUS_CLIENT_SECRET"]
        self.base_url = base_url
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._http = httpx.Client(timeout=30)

    # --- auth -----------------------------------------------------------

    def _get_token(self) -> str:
        """Return a valid access token, fetching a new one if needed."""
        # Refresh 60s early to avoid using a token that expires mid-request.
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token

        resp = self._http.post(
            f"{self.base_url}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200:
            raise AmadeusError(f"Auth failed ({resp.status_code}): {resp.text}")

        payload = resp.json()
        self._token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 1799)
        return self._token

    # --- endpoints ------------------------------------------------------

    def search_flight_offers(
        self,
        origin: str,
        destination: str,
        departure_date: str,  # YYYY-MM-DD
        adults: int = 1,
        currency: str = "USD",
        max_results: int = 10,
        non_stop: bool = False,
    ) -> dict:
        """Search one-way flight offers for a route on a given date.

        Returns the raw API response as a dict. We keep it raw on purpose:
        the ingestion layer's job is to capture data faithfully; cleaning
        happens later in dbt.
        """
        resp = self._http.get(
            f"{self.base_url}/v2/shopping/flight-offers",
            params={
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "currencyCode": currency,
                "max": max_results,
                "nonStop": str(non_stop).lower(),
            },
            headers={"Authorization": f"Bearer {self._get_token()}"},
        )
        if resp.status_code != 200:
            raise AmadeusError(
                f"Flight search failed ({resp.status_code}) for "
                f"{origin}->{destination} on {departure_date}: {resp.text}"
            )
        return resp.json()

    def close(self) -> None:
        self._http.close()
