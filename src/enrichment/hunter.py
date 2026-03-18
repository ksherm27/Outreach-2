from __future__ import annotations

from dataclasses import dataclass

import httpx

from src.config.settings import get_settings
from src.shared.exceptions import HunterError
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EmailResult:
    email: str
    confidence: float
    first_name: str | None = None
    last_name: str | None = None
    position: str | None = None
    linkedin_url: str | None = None


@dataclass
class VerificationResult:
    email: str
    status: str  # valid, invalid, accept_all, unknown
    score: int


class HunterClient:
    """Client for the Hunter.io API."""

    BASE_URL = "https://api.hunter.io/v2"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.hunter_api_key

    def find_email(
        self,
        domain: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> EmailResult | None:
        """Find an email for a person at a domain."""
        if not self.api_key:
            logger.warning("hunter_api_key_not_configured")
            return None

        params: dict = {
            "domain": domain,
            "api_key": self.api_key,
        }
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name

        try:
            with httpx.Client(timeout=15) as client:
                response = client.get(f"{self.BASE_URL}/email-finder", params=params)
                if response.status_code != 200:
                    raise HunterError(f"Hunter API returned {response.status_code}")

                data = response.json().get("data", {})
                email = data.get("email")
                if not email:
                    return None

                return EmailResult(
                    email=email,
                    confidence=data.get("confidence", 0) / 100.0,
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    position=data.get("position"),
                    linkedin_url=data.get("linkedin"),
                )
        except httpx.RequestError as e:
            raise HunterError(f"Hunter request failed: {e}") from e

    def domain_search(self, domain: str, limit: int = 10) -> list[EmailResult]:
        """Search for all emails at a domain."""
        if not self.api_key:
            return []

        params = {
            "domain": domain,
            "api_key": self.api_key,
            "limit": limit,
            "type": "personal",
        }

        try:
            with httpx.Client(timeout=15) as client:
                response = client.get(f"{self.BASE_URL}/domain-search", params=params)
                if response.status_code != 200:
                    raise HunterError(f"Hunter API returned {response.status_code}")

                data = response.json().get("data", {})
                emails = data.get("emails", [])

                return [
                    EmailResult(
                        email=e["value"],
                        confidence=e.get("confidence", 0) / 100.0,
                        first_name=e.get("first_name"),
                        last_name=e.get("last_name"),
                        position=e.get("position"),
                        linkedin_url=e.get("linkedin"),
                    )
                    for e in emails
                    if e.get("value")
                ]
        except httpx.RequestError as e:
            raise HunterError(f"Hunter request failed: {e}") from e

    def verify_email(self, email: str) -> VerificationResult | None:
        """Verify an email address."""
        if not self.api_key:
            return None

        params = {"email": email, "api_key": self.api_key}

        try:
            with httpx.Client(timeout=15) as client:
                response = client.get(f"{self.BASE_URL}/email-verifier", params=params)
                if response.status_code != 200:
                    raise HunterError(f"Hunter API returned {response.status_code}")

                data = response.json().get("data", {})
                return VerificationResult(
                    email=email,
                    status=data.get("status", "unknown"),
                    score=data.get("score", 0),
                )
        except httpx.RequestError as e:
            raise HunterError(f"Hunter request failed: {e}") from e
