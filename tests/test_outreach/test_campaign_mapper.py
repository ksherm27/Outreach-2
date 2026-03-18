"""Tests for campaign mapper."""

from unittest.mock import MagicMock, patch

from src.config.constants import GTMRoleCategory


class TestCampaignMapper:
    def test_maps_category_to_campaign(self):
        from src.outreach.campaign_mapper import get_campaign_ids

        with patch("src.outreach.campaign_mapper.get_settings") as mock:
            mock.return_value = MagicMock(
                instantly=MagicMock(
                    campaign_map={
                        "Sales Leadership": "camp_sales",
                        "default": "camp_default",
                    },
                    default_campaign_id="camp_fallback",
                ),
                lemlist=MagicMock(
                    campaign_map={
                        "Sales Leadership": "lem_sales",
                        "default": "lem_default",
                    },
                ),
            )
            ids = get_campaign_ids(GTMRoleCategory.SALES_LEADERSHIP)
            assert ids.instantly_campaign_id == "camp_sales"
            assert ids.lemlist_campaign_id == "lem_sales"

    def test_falls_back_to_default(self):
        from src.outreach.campaign_mapper import get_campaign_ids

        with patch("src.outreach.campaign_mapper.get_settings") as mock:
            mock.return_value = MagicMock(
                instantly=MagicMock(
                    campaign_map={
                        "default": "camp_default",
                    },
                    default_campaign_id="camp_fallback",
                ),
                lemlist=MagicMock(
                    campaign_map={
                        "default": "lem_default",
                    },
                ),
            )
            ids = get_campaign_ids(GTMRoleCategory.CS_LEADERSHIP)
            assert ids.instantly_campaign_id == "camp_default"
            assert ids.lemlist_campaign_id == "lem_default"
