from __future__ import annotations

import httpx

from src.config.settings import get_settings
from src.shared.exceptions import LemlistError
from src.shared.logging import get_logger

logger = get_logger(__name__)


class LemlistClient:
    """Client for the Lemlist API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.lemlist_api_key
        self.base_url = settings.lemlist.api_base_url

    def _request(self, method: str, path: str, **kwargs) -> dict | list:
        """Make an authenticated request to the Lemlist API."""
        if not self.api_key:
            raise LemlistError("Lemlist API key not configured")

        url = f"{self.base_url}{path}"

        try:
            with httpx.Client(timeout=15) as client:
                response = client.request(
                    method,
                    url,
                    auth=("", self.api_key),
                    **kwargs,
                )
                if response.status_code >= 400:
                    raise LemlistError(
                        f"Lemlist API error {response.status_code}: {response.text}"
                    )
                return response.json() if response.text else {}
        except httpx.RequestError as e:
            raise LemlistError(f"Lemlist request failed: {e}") from e

    def add_lead(
        self,
        campaign_id: str,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        company_name: str | None = None,
        variables: dict | None = None,
    ) -> dict:
        """Add a lead to a Lemlist campaign."""
        payload: dict = {"email": email}
        if first_name:
            payload["firstName"] = first_name
        if last_name:
            payload["lastName"] = last_name
        if company_name:
            payload["companyName"] = company_name
        if variables:
            payload.update(variables)

        result = self._request(
            "POST",
            f"/campaigns/{campaign_id}/leads/{email}",
            json=payload,
        )
        logger.info("lemlist_lead_added", email=email, campaign=campaign_id)
        return result if isinstance(result, dict) else {}

    def pause_lead(self, campaign_id: str, email: str) -> dict:
        """Pause a lead in a campaign."""
        result = self._request(
            "POST",
            f"/campaigns/{campaign_id}/leads/{email}/pause",
        )
        logger.info("lemlist_lead_paused", email=email, campaign=campaign_id)
        return result if isinstance(result, dict) else {}

    def resume_lead(self, campaign_id: str, email: str) -> dict:
        """Resume a paused lead."""
        result = self._request(
            "POST",
            f"/campaigns/{campaign_id}/leads/{email}/resume",
        )
        logger.info("lemlist_lead_resumed", email=email, campaign=campaign_id)
        return result if isinstance(result, dict) else {}

    def delete_lead(self, campaign_id: str, email: str) -> dict:
        """Remove a lead from a campaign."""
        result = self._request(
            "DELETE",
            f"/campaigns/{campaign_id}/leads/{email}",
        )
        logger.info("lemlist_lead_deleted", email=email, campaign=campaign_id)
        return result if isinstance(result, dict) else {}

    def get_campaign_activities(self, campaign_id: str) -> list[dict]:
        """Get activities (including replies) for a campaign."""
        result = self._request("GET", f"/campaigns/{campaign_id}/export")
        return result if isinstance(result, list) else []

    def list_campaigns(self) -> list[dict]:
        """List all campaigns."""
        result = self._request("GET", "/campaigns")
        return result if isinstance(result, list) else []
