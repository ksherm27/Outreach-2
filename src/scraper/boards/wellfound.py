from __future__ import annotations

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("wellfound")
class WellfoundScraper(BaseScraper):
    """Scrapes Wellfound (formerly AngelList) job listings.

    Wellfound is JS-heavy; this scraper uses their GraphQL-like API endpoint
    or falls back to Playwright for rendering.
    """

    BASE_URL = "https://wellfound.com"
    SEARCH_URL = "https://wellfound.com/role/l/{role}"

    def scrape(self, search_queries: list[str]) -> list[RawJobData]:
        logger.info("wellfound_scraper_started", queries=search_queries)
        # Wellfound requires JS rendering - placeholder for Playwright implementation
        return []
