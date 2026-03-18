"""Tests for ICP scoring engine."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.config.settings import ScoringWeights, RoleConfig


class TestICPScoring:
    """Test ICP scoring logic in isolation."""

    def test_title_exact_match_scores_highest(self):
        """Exact title matches should get the highest title score."""
        from src.scoring.icp import ICPScorer

        with patch("src.scoring.icp.get_settings") as mock:
            mock.return_value = MagicMock(
                icp=MagicMock(
                    target_roles={
                        "Sales Leadership": RoleConfig(
                            score=35,
                            titles=["VP of Sales", "Head of Sales"],
                        ),
                    },
                    scoring=ScoringWeights(
                        title_exact_match=35,
                        title_fuzzy_match=20,
                        funding_crunchbase_confirmed=25,
                        funding_keyword_in_jd=15,
                        saas_keyword_confirmed=20,
                        employee_count_25_to_500=10,
                        employee_count_500_to_1000=5,
                        posted_within_48h=10,
                        posted_48h_to_72h=5,
                        target_location=5,
                        staffing_agency_detected=-50,
                        public_company_detected=-40,
                    ),
                    funding_signals=["Series B"],
                    saas_signals=["SaaS"],
                    target_locations=["United States"],
                    target_funding_stages=["Series A", "Series B"],
                    exclude_signals=[],
                )
            )
            scorer = ICPScorer()
            score = scorer._title_score("VP of Sales")
            assert score == 35

    def test_title_fuzzy_match_scores_lower(self):
        """Fuzzy title matches should get a lower score."""
        from src.scoring.icp import ICPScorer

        with patch("src.scoring.icp.get_settings") as mock:
            mock.return_value = MagicMock(
                icp=MagicMock(
                    target_roles={
                        "Sales Leadership": RoleConfig(
                            score=35,
                            titles=["VP of Sales"],
                        ),
                    },
                    scoring=ScoringWeights(
                        title_exact_match=35,
                        title_fuzzy_match=20,
                        funding_crunchbase_confirmed=25,
                        funding_keyword_in_jd=15,
                        saas_keyword_confirmed=20,
                        employee_count_25_to_500=10,
                        employee_count_500_to_1000=5,
                        posted_within_48h=10,
                        posted_48h_to_72h=5,
                        target_location=5,
                        staffing_agency_detected=-50,
                        public_company_detected=-40,
                    ),
                    funding_signals=[],
                    saas_signals=[],
                    target_locations=[],
                    target_funding_stages=[],
                    exclude_signals=[],
                )
            )
            scorer = ICPScorer()
            score = scorer._title_score("Senior VP of Sales - Enterprise")
            assert score == 20

    def test_no_title_match_scores_zero(self):
        """Non-matching titles should score zero."""
        from src.scoring.icp import ICPScorer

        with patch("src.scoring.icp.get_settings") as mock:
            mock.return_value = MagicMock(
                icp=MagicMock(
                    target_roles={
                        "Sales Leadership": RoleConfig(
                            score=35,
                            titles=["VP of Sales"],
                        ),
                    },
                    scoring=ScoringWeights(
                        title_exact_match=35,
                        title_fuzzy_match=20,
                        funding_crunchbase_confirmed=25,
                        funding_keyword_in_jd=15,
                        saas_keyword_confirmed=20,
                        employee_count_25_to_500=10,
                        employee_count_500_to_1000=5,
                        posted_within_48h=10,
                        posted_48h_to_72h=5,
                        target_location=5,
                        staffing_agency_detected=-50,
                        public_company_detected=-40,
                    ),
                    funding_signals=[],
                    saas_signals=[],
                    target_locations=[],
                    target_funding_stages=[],
                    exclude_signals=[],
                )
            )
            scorer = ICPScorer()
            score = scorer._title_score("Software Engineer")
            assert score == 0

    def test_staffing_agency_penalty(self):
        """Staffing agencies should get a large negative penalty."""
        from src.scoring.icp import ICPScorer

        with patch("src.scoring.icp.get_settings") as mock:
            mock.return_value = MagicMock(
                icp=MagicMock(
                    target_roles={},
                    scoring=ScoringWeights(
                        title_exact_match=35,
                        title_fuzzy_match=20,
                        funding_crunchbase_confirmed=25,
                        funding_keyword_in_jd=15,
                        saas_keyword_confirmed=20,
                        employee_count_25_to_500=10,
                        employee_count_500_to_1000=5,
                        posted_within_48h=10,
                        posted_48h_to_72h=5,
                        target_location=5,
                        staffing_agency_detected=-50,
                        public_company_detected=-40,
                    ),
                    funding_signals=[],
                    saas_signals=[],
                    target_locations=[],
                    target_funding_stages=[],
                    exclude_signals=[],
                )
            )
            scorer = ICPScorer()
            penalty = scorer._exclusion_penalties(
                "We are a staffing agency specializing in tech", "TalentCo"
            )
            assert penalty == -50
