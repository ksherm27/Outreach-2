from __future__ import annotations

import httpx

from src.config.settings import get_settings
from src.shared.exceptions import InstantlyError
from src.shared.logging import get_logger

logger = get_logger(__name__)


class InstantlyClient:
    """Client for the Instantly.ai API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.instantly_api_key
        self.base_url = settings.instantly.api_base_url

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an authenticated request to the Instantly API."""
        if not self.api_key:
            raise InstantlyError("Instantly API key not configured")

        url = f"{self.base_url}{path}"
        params = kwargs.pop("params", {})
        params["api_key"] = self.api_key

        try:
            with httpx.Client(timeout=15) as client:
                response = client.request(method, url, params=params, **kwargs)
                if response.status_code >= 400:
                    raise InstantlyError(
                        f"Instantly API error {response.status_code}: {response.text}"
                    )
                return response.json() if response.text else {}
        except httpx.RequestError as e:
            raise InstantlyError(f"Instantly request failed: {e}") from e

    def add_lead(
        self,
        campaign_id: str,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        company_name: str | None = None,
        variables: dict | None = None,
    ) -> dict:
        """Add a lead to an Instantly campaign."""
        payload: dict = {
            "campaign_id": campaign_id,
            "email": email,
        }
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name
        if company_name:
            payload["company_name"] = company_name
        if variables:
            payload["variables"] = variables

        result = self._request("POST", "/lead/add", json=payload)
        logger.info("instantly_lead_added", email=email, campaign=campaign_id)
        return result

    def pause_lead(self, campaign_id: str, email: str) -> dict:
        """Pause a lead in a campaign."""
        payload = {"campaign_id": campaign_id, "email": email}
        result = self._request("POST", "/lead/pause", json=payload)
        logger.info("instantly_lead_paused", email=email, campaign=campaign_id)
        return result

    def resume_lead(self, campaign_id: str, email: str) -> dict:
        """Resume a paused lead in a campaign."""
        payload = {"campaign_id": campaign_id, "email": email}
        result = self._request("POST", "/lead/resume", json=payload)
        logger.info("instantly_lead_resumed", email=email, campaign=campaign_id)
        return result

    def delete_lead(self, campaign_id: str, email: str) -> dict:
        """Delete a lead from a campaign (for unsubscribes)."""
        payload = {"campaign_id": campaign_id, "email": email, "delete_all_from_company": False}
        result = self._request("POST", "/lead/delete", json=payload)
        logger.info("instantly_lead_deleted", email=email, campaign=campaign_id)
        return result

    def get_campaign_replies(self, campaign_id: str) -> list[dict]:
        """Get replies for a campaign."""
        result = self._request("GET", "/unibox/emails", params={"campaign_id": campaign_id})
        return result.get("data", [])

    def list_campaigns(self) -> list[dict]:
        """List all campaigns."""
        result = self._request("GET", "/campaign/list")
        return result if isinstance(result, list) else result.get("data", [])
