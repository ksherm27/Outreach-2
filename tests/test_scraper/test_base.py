"""Tests for the base scraper functionality."""

from unittest.mock import MagicMock, patch

import pytest

from src.scraper.base import BaseScraper, RawJobData


class ConcreteScraper(BaseScraper):
    board_name = "test"

    def scrape(self, search_queries):
        return []


class TestBaseScraper:
    def test_matches_keywords(self):
        """Scrapers should be instantiable."""
        with patch("src.scraper.base.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                scraping=MagicMock(
                    user_agents=["TestAgent/1.0"],
                    request_delay_min_seconds=0,
                    request_delay_max_seconds=0,
                    respect_robots_txt=False,
                )
            )
            scraper = ConcreteScraper()
            assert scraper.board_name == "test"

    def test_raw_job_data_creation(self):
        """RawJobData should be creatable with required fields."""
        job = RawJobData(
            title="VP of Sales",
            company_name="TestCo",
            source_url="https://example.com/jobs/1",
            board_name="greenhouse",
        )
        assert job.title == "VP of Sales"
        assert job.location is None
        assert job.description is None
