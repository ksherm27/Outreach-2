from __future__ import annotations

from dataclasses import dataclass

import httpx

from src.config.settings import get_settings
from src.enrichment.cache import cache_get, cache_set
from src.shared.exceptions import CrunchbaseError
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CompanyData:
    name: str
    domain: str | None = None
    funding_stage: str | None = None
    total_raised: int | None = None
    employee_count: int | None = None
    founded_year: int | None = None
    hq_location: str | None = None
    description: str | None = None
    is_public: bool = False
    industry: str | None = None
    crunchbase_id: str | None = None


class CrunchbaseClient:
    """Client for the Crunchbase API."""

    BASE_URL = "https://api.crunchbase.com/api/v4"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.crunchbase_api_key
        self.cache_ttl = settings.enrichment.crunchbase_cache_ttl_days

    def get_company(self, domain: str) -> CompanyData | None:
        """Look up a company by domain. Uses cache if available."""
        if not self.api_key:
            logger.warning("crunchbase_api_key_not_configured")
            return None

        cache_key = f"crunchbase:domain:{domain}"
        cached = cache_get(cache_key)
        if cached:
            return CompanyData(**cached)

        try:
            data = self._search_by_domain(domain)
            if data:
                cache_set(cache_key, data.__dict__, self.cache_ttl)
            return data
        except Exception as e:
            raise CrunchbaseError(f"Failed to lookup {domain}: {e}") from e

    def _search_by_domain(self, domain: str) -> CompanyData | None:
        """Search Crunchbase for a company by website domain."""
        url = f"{self.BASE_URL}/autocompletes"
        params = {
            "query": domain,
            "collection_ids": "organizations",
            "limit": 1,
            "user_key": self.api_key,
        }

        with httpx.Client(timeout=15) as client:
            response = client.get(url, params=params)
            if response.status_code != 200:
                raise CrunchbaseError(f"API returned {response.status_code}")

            data = response.json()
            entities = data.get("entities", [])
            if not entities:
                return None

            entity = entities[0]
            org_id = entity.get("identifier", {}).get("permalink", "")

            # Fetch full organization details
            return self._get_organization(org_id)

    def _get_organization(self, org_id: str) -> CompanyData | None:
        """Fetch full organization details from Crunchbase."""
        url = f"{self.BASE_URL}/entities/organizations/{org_id}"
        params = {
            "card_ids": "fields",
            "field_ids": (
                "short_description,num_employees_enum,founded_on,"
                "funding_total,last_funding_type,location_identifiers,"
                "website_url,categories,ipo_status,identifier"
            ),
            "user_key": self.api_key,
        }

        with httpx.Client(timeout=15) as client:
            response = client.get(url, params=params)
            if response.status_code != 200:
                return None

            data = response.json()
            properties = data.get("properties", {})

            # Parse employee count from enum
            emp_enum = properties.get("num_employees_enum", "")
            employee_count = self._parse_employee_enum(emp_enum)

            # Parse funding
            funding_total = properties.get("funding_total", {})
            total_raised = None
            if funding_total and funding_total.get("value_usd"):
                total_raised = int(funding_total["value_usd"])

            # Parse location
            locations = properties.get("location_identifiers", [])
            hq_location = ""
            if locations:
                hq_location = locations[0].get("value", "")

            # Parse founded year
            founded_on = properties.get("founded_on", "")
            founded_year = None
            if founded_on:
                try:
                    founded_year = int(founded_on.split("-")[0])
                except (ValueError, IndexError):
                    pass

            return CompanyData(
                name=properties.get("identifier", {}).get("value", org_id),
                domain=properties.get("website_url", ""),
                funding_stage=properties.get("last_funding_type", ""),
                total_raised=total_raised,
                employee_count=employee_count,
                founded_year=founded_year,
                hq_location=hq_location,
                description=properties.get("short_description", ""),
                is_public=properties.get("ipo_status") == "public",
                crunchbase_id=org_id,
            )

    def _parse_employee_enum(self, enum_val: str) -> int | None:
        """Parse Crunchbase employee count enum to an integer midpoint."""
        mapping = {
            "c_00001_00010": 5,
            "c_00011_00050": 30,
            "c_00051_00100": 75,
            "c_00101_00250": 175,
            "c_00251_00500": 375,
            "c_00501_01000": 750,
            "c_01001_05000": 3000,
            "c_05001_10000": 7500,
            "c_10001_max": 15000,
        }
        return mapping.get(enum_val)
