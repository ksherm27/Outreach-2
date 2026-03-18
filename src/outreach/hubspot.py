from __future__ import annotations

import httpx

from src.config.settings import get_settings
from src.shared.exceptions import HubSpotError
from src.shared.logging import get_logger

logger = get_logger(__name__)


class HubSpotClient:
    """Client for the HubSpot CRM API."""

    BASE_URL = "https://api.hubapi.com"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.hubspot_api_key
        self.pipeline_id = settings.crm.hubspot.get("pipeline_id", "default")
        self.stage_map = settings.crm.hubspot.get("stage_map", {})

    def _request(self, method: str, path: str, **kwargs) -> dict:
        if not self.api_key:
            raise HubSpotError("HubSpot API key not configured")

        url = f"{self.BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=15) as client:
                response = client.request(method, url, headers=headers, **kwargs)
                if response.status_code >= 400:
                    raise HubSpotError(
                        f"HubSpot API error {response.status_code}: {response.text}"
                    )
                return response.json() if response.text else {}
        except httpx.RequestError as e:
            raise HubSpotError(f"HubSpot request failed: {e}") from e

    def create_or_update_contact(self, email: str, properties: dict) -> dict:
        """Create or update a HubSpot contact."""
        # Try to find existing contact
        try:
            result = self._request(
                "POST",
                "/crm/v3/objects/contacts/search",
                json={
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email,
                        }]
                    }]
                },
            )
            existing = result.get("results", [])
            if existing:
                contact_id = existing[0]["id"]
                self._request(
                    "PATCH",
                    f"/crm/v3/objects/contacts/{contact_id}",
                    json={"properties": properties},
                )
                logger.info("hubspot_contact_updated", email=email, contact_id=contact_id)
                return {"id": contact_id, "action": "updated"}
        except HubSpotError:
            pass

        # Create new contact
        properties["email"] = email
        result = self._request(
            "POST",
            "/crm/v3/objects/contacts",
            json={"properties": properties},
        )
        contact_id = result.get("id", "")
        logger.info("hubspot_contact_created", email=email, contact_id=contact_id)
        return {"id": contact_id, "action": "created"}

    def create_deal(
        self,
        deal_name: str,
        stage: str,
        contact_id: str | None = None,
        properties: dict | None = None,
    ) -> dict:
        """Create a HubSpot deal and optionally associate with a contact."""
        stage_id = self.stage_map.get(stage, stage)

        deal_properties = {
            "dealname": deal_name,
            "pipeline": self.pipeline_id,
            "dealstage": stage_id,
        }
        if properties:
            deal_properties.update(properties)

        payload: dict = {"properties": deal_properties}

        if contact_id:
            payload["associations"] = [{
                "to": {"id": contact_id},
                "types": [{
                    "associationCategory": "HUBSPOT_DEFINED",
                    "associationTypeId": 3,  # Deal-to-Contact
                }],
            }]

        result = self._request("POST", "/crm/v3/objects/deals", json=payload)
        deal_id = result.get("id", "")
        logger.info("hubspot_deal_created", deal_id=deal_id, stage=stage)
        return {"id": deal_id}

    def update_deal_stage(self, deal_id: str, stage: str) -> dict:
        """Update a deal's stage."""
        stage_id = self.stage_map.get(stage, stage)
        result = self._request(
            "PATCH",
            f"/crm/v3/objects/deals/{deal_id}",
            json={"properties": {"dealstage": stage_id}},
        )
        logger.info("hubspot_deal_stage_updated", deal_id=deal_id, stage=stage)
        return result

    def add_note(self, deal_id: str, content: str) -> dict:
        """Add a note to a deal."""
        note = self._request(
            "POST",
            "/crm/v3/objects/notes",
            json={
                "properties": {"hs_note_body": content},
                "associations": [{
                    "to": {"id": deal_id},
                    "types": [{
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 214,  # Note-to-Deal
                    }],
                }],
            },
        )
        logger.info("hubspot_note_added", deal_id=deal_id)
        return note
