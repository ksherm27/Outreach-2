from __future__ import annotations

from src.config.constants import GTMRoleCategory
from src.config.settings import get_settings


def categorize_role(title: str) -> GTMRoleCategory | None:
    """Map a job title to a GTM role category. Returns None if no match."""
    settings = get_settings()
    title_lower = title.lower().strip()

    best_match: GTMRoleCategory | None = None
    best_score = 0

    category_map = {
        "Sales Leadership": GTMRoleCategory.SALES_LEADERSHIP,
        "Marketing Leadership": GTMRoleCategory.MARKETING_LEADERSHIP,
        "Customer Success Leadership": GTMRoleCategory.CS_LEADERSHIP,
        "GTM Strategy": GTMRoleCategory.GTM_STRATEGY,
        "SDR BDR Leadership": GTMRoleCategory.SDR_BDR_LEADERSHIP,
    }

    for category_name, role_config in settings.icp.target_roles.items():
        enum_val = category_map.get(category_name)
        if not enum_val:
            continue

        for target_title in role_config.titles:
            target_lower = target_title.lower()
            # Exact match gets highest priority
            if target_lower == title_lower:
                return enum_val
            # Fuzzy match — target title is a substring of job title
            if target_lower in title_lower and role_config.score > best_score:
                best_match = enum_val
                best_score = role_config.score

    return best_match
