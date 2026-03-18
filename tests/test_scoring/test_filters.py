"""Tests for exclusion filters."""

from unittest.mock import MagicMock, patch

import pytest


class TestExclusionFilter:
    def test_exclude_staffing_agency(self):
        from src.scoring.filters import ExclusionFilter

        with patch("src.scoring.filters.get_settings") as mock:
            mock.return_value = MagicMock(
                icp=MagicMock(
                    exclude_signals=["staffing agency", "recruiting firm"],
                    min_employees=25,
                    max_employees=1000,
                )
            )
            f = ExclusionFilter()
            job = MagicMock(
                company_name="TalentStaff",
                title="VP Sales",
                description="We are a staffing agency",
            )
            excluded, reason = f.should_exclude(job)
            assert excluded is True
            assert "staffing agency" in reason

    def test_allow_saas_company(self):
        from src.scoring.filters import ExclusionFilter

        with patch("src.scoring.filters.get_settings") as mock:
            mock.return_value = MagicMock(
                icp=MagicMock(
                    exclude_signals=["staffing agency"],
                    min_employees=25,
                    max_employees=1000,
                )
            )
            f = ExclusionFilter()
            job = MagicMock(
                company_name="SaaSCo",
                title="VP Sales",
                description="B2B SaaS platform for developers",
            )
            excluded, reason = f.should_exclude(job)
            assert excluded is False
