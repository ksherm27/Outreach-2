from __future__ import annotations

from dataclasses import dataclass

import httpx

from src.config.settings import get_settings
from src.shared.exceptions import RocketReachError
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PersonResult:
    name: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    email_confidence: float = 0.0
    title: str | None = None
    linkedin_url: str | None = None
    phone: str | None = None


class RocketReachClient:
    """Client for the RocketReach API."""

    BASE_URL = "https://api.rocketreach.co/api/v2"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.rocketreach_api_key

    def _headers(self) -> dict[str, str]:
        return {"RocketReachAPIKey": self.api_key, "Content-Type": "application/json"}

    def person_search(
        self,
        company_name: str,
        title_keywords: list[str] | None = None,
        max_results: int = 10,
    ) -> list[PersonResult]:
        """Search for people at a company by title keywords."""
        if not self.api_key:
            logger.warning("rocketreach_api_key_not_configured")
            return []

        query: dict = {"current_employer": [company_name]}
        if title_keywords:
            query["current_title"] = title_keywords

        payload = {"query": query, "page_size": max_results}

        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(
                    f"{self.BASE_URL}/person/search",
                    headers=self._headers(),
                    json=payload,
                )
                if response.status_code == 429:
                    raise RocketReachError("RocketReach rate limit exceeded")
                if response.status_code != 200:
                    raise RocketReachError(
                        f"RocketReach API returned {response.status_code}: {response.text[:200]}"
                    )

                data = response.json()
                profiles = data.get("profiles", [])
                return [self._parse_person(p) for p in profiles]

        except httpx.RequestError as e:
            raise RocketReachError(f"RocketReach request failed: {e}") from e

    def person_lookup(
        self,
        name: str | None = None,
        company: str | None = None,
        linkedin_url: str | None = None,
    ) -> PersonResult | None:
        """Look up a specific person by name+company or LinkedIn URL."""
        if not self.api_key:
            logger.warning("rocketreach_api_key_not_configured")
            return None

        params: dict = {}
        if linkedin_url:
            params["linkedin_url"] = linkedin_url
        elif name and company:
            params["name"] = name
            params["current_employer"] = company
        else:
            return None

        try:
            with httpx.Client(timeout=15) as client:
                response = client.get(
                    f"{self.BASE_URL}/person/lookup",
                    headers=self._headers(),
                    params=params,
                )
                if response.status_code == 404:
                    return None
                if response.status_code != 200:
                    raise RocketReachError(
                        f"RocketReach API returned {response.status_code}"
                    )

                data = response.json()
                return self._parse_person(data)

        except httpx.RequestError as e:
            raise RocketReachError(f"RocketReach request failed: {e}") from e

    def _parse_person(self, data: dict) -> PersonResult:
        """Parse a person profile from the API response."""
        emails = data.get("emails", [])
        best_email = None
        best_confidence = 0.0

        for email_entry in emails:
            if isinstance(email_entry, dict):
                addr = email_entry.get("email", "")
                smtp_valid = email_entry.get("smtp_valid", "")
                confidence = 0.9 if smtp_valid == "valid" else 0.5
            elif isinstance(email_entry, str):
                addr = email_entry
                confidence = 0.5
            else:
                continue

            if addr and confidence > best_confidence:
                best_email = addr
                best_confidence = confidence

        phones = data.get("phones", [])
        phone = None
        if phones:
            first_phone = phones[0]
            phone = first_phone.get("number") if isinstance(first_phone, dict) else str(first_phone)

        name = data.get("name", "")
        first_name = data.get("first_name") or (name.split()[0] if name else None)
        last_name = data.get("last_name") or (name.split()[-1] if name and len(name.split()) > 1 else None)

        return PersonResult(
            name=name,
            first_name=first_name,
            last_name=last_name,
            email=best_email,
            email_confidence=best_confidence,
            title=data.get("current_title"),
            linkedin_url=data.get("linkedin_url"),
            phone=phone,
        )
