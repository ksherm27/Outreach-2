from __future__ import annotations

from dataclasses import dataclass

from src.config.constants import GTMRoleCategory
from src.config.settings import get_settings


@dataclass
class CampaignIds:
    instantly_campaign_id: str
    lemlist_campaign_id: str


def get_campaign_ids(category: GTMRoleCategory | str) -> CampaignIds:
    """Map a GTM role category to Instantly and Lemlist campaign IDs."""
    settings = get_settings()

    category_str = category.value if isinstance(category, GTMRoleCategory) else category

    instantly_id = (
        settings.instantly.campaign_map.get(category_str)
        or settings.instantly.campaign_map.get("default", "")
        or settings.instantly.default_campaign_id
    )

    lemlist_id = (
        settings.lemlist.campaign_map.get(category_str)
        or settings.lemlist.campaign_map.get("default", "")
    )

    return CampaignIds(
        instantly_campaign_id=instantly_id,
        lemlist_campaign_id=lemlist_id,
    )
